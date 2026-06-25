"""Diagnostics on raw and adjusted simulation."""
import copy
import os
from copy import deepcopy

import xarray as xr
import xscen as xs

from workflow.scripts.utils import dask_cluster


if 1 == 0:  # trick vscode
    import snakemake
xr.set_options(
    netcdf_engine_order=[
        "h5netcdf",
        "netcdf4",
    ]
)


if __name__ == "__main__":
    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs = snakemake.input
    dregion = snakemake.wildcards.dregion
    sim_id = snakemake.wildcards.sim_id
    output = snakemake.output

    client = dask_cluster(snakemake.params, config["dask"]["client"])

    # load data that we already have
    ref_prop = xr.open_zarr(inputs["ref_prop"], decode_timedelta=False)

    ds_scen = xr.open_mfdataset(
        [
            inputs[f"scen_{v}"]
            for v in config["diagnostics"]["properties_and_measures"][
                "change_units_arg"
            ].keys()
        ],
        engine="zarr",
        decode_timedelta=False,
    )
    ds_scen = xs.spatial.subset(ds_scen, **config["diagregion"][dregion])

    # Create ds_sim for full region
    args = copy.deepcopy(config["extraction"]["simulation"]["search_data_catalogs"])
    args["other_search_criteria"] = {"id": sim_id}
    cat_sim_id = xs.search_data_catalogs(
        **args,
    )
    dc_id = cat_sim_id.popitem()[1]
    region_dict = config["full_region"]
    ds_sim = xs.extract_dataset(
        catalog=dc_id,
        region=region_dict,
        **config["extraction"]["simulation"]["extract_dataset"],
    )["D"]
    ds_sim["time"] = ds_sim.time.dt.floor(
        "D"
    )  # probably this wont be need when data is cleaned
    # need lat and lon -1 for the regrid
    ds_sim = xs.io.rechunk_for_saving(ds_sim, rechunk=config["chunks"]["pre-regrid"])
    if "hursmin" in ds_sim:
        ds_sim = ds_sim.rename({"hursmin": "hursTasmax"})

    # get target ref grid
    ds_target = xr.open_zarr(inputs["ref"], decode_timedelta=False)
    ds_target = xs.spatial.subset(ds_target, **config["diagregion"][dregion])

    # regrid
    args = config["regrid"]["regrid_dataset"].copy()
    args["regridder_kwargs"]["locstream_out"] = False
    ds_sim = xs.regrid_dataset(
        ds=ds_sim,
        ds_grid=ds_target,
        weights_location=f"{os.environ['SLURM_TMPDIR']}/weights/",
        **args,
    )
    # mask nan
    mask = ds_target["tasmax"].isel(time=130, drop=True).notnull().compute()
    ds_sim = ds_sim.where(mask)

    # chunk
    ds_sim = xs.io.rechunk_for_saving(ds_sim, config["chunks"]["workingXY"])
    ds_scen = xs.io.rechunk_for_saving(ds_scen, config["chunks"]["workingXY"])

    with xr.set_options(keep_attrs=True):  # to keep grid_mapping and bias_adj attr
        sim_prop, sim_meas = xs.properties_and_measures(
            ds=ds_sim,
            dref_for_measure=ref_prop,
            **config["diagnostics"]["properties_and_measures"],
        )

        scen_prop, scen_meas = xs.properties_and_measures(
            ds=ds_scen,
            dref_for_measure=ref_prop,
            **config["diagnostics"]["properties_and_measures"],
        )
    for out, name in zip(
        [sim_prop, sim_meas, scen_prop, scen_meas],
        ["sim_prop", "sim_meas", "scen_prop", "scen_meas"],
        strict=True,
    ):
        xs.save_to_zarr(
            out,
            output[name],
            **config["save_to_zarr"],
            rechunk=config["chunks"]["diag"],
        )

    imp = xs.diagnostics.measures_improvement([sim_meas, scen_meas])

    xs.save_to_zarr(imp, output["imp"], **config["save_to_zarr"])
