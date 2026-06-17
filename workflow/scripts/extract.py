"""Search catalog, extract simulation on the right region and clean it up."""

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
    pool = snakemake.wildcards.pool
    output = snakemake.output

    client = dask_cluster(snakemake.params, config["dask"]["client"])

    args = deepcopy(config["extraction"]["simulation"]["search_data_catalogs"])

    # get right sims from pool name
    poolsplit = pool.split("_")
    if poolsplit[0] == "ScenarioMIP":  # GCM
        args["other_search_criteria"] = {
            "source": poolsplit[1],
            "experiment": poolsplit[2],
        }
    else:  # RCM
        args["other_search_criteria"] = {
            "source": poolsplit[0],
            "experiment": poolsplit[2],
            "driving_model": poolsplit[1],
        }
    # search cat
    cat_sim_id = xs.search_data_catalogs(
        **args,
    )

    # extract all the member
    real = []
    for subcat in cat_sim_id.values():
        dict_sim = xs.extract_dataset(
            catalog=subcat,
            region=config["full_region"],
            **config["extraction"]["simulation"]["extract_dataset"],
        )
        ds_r = dict_sim["D"]
        ds_r = ds_r.expand_dims(realization=[ds_r.attrs["cat:id"]])
        real.append(ds_r)

    ds_sim = xr.concat(real, dim="realization")

    # nan weird individual timestep
    if "BCC-CSM2-MR" in pool:  # dtr around -30
        ds_sim["tasmin"] = ds_sim["tasmin"].where(
            ds_sim.time != (ds_sim.time.sel(time="2014-12-31").values),
        )
        ds_sim["dtr"] = ds_sim["dtr"].where(
            ds_sim.time != (ds_sim.time.sel(time="2014-12-31").values),
        )
    if "ACCESS-ESM1-5" in pool:  # tasmin -138
        ds_sim["tasmin"] = ds_sim["tasmin"].where(
            ~(
                (ds_sim.lat == 63.75)
                & (ds_sim.lon == 313.125)
                & (ds_sim.time == ds_sim.time.sel(time="1984-01-10").values)
            )
        )
        ds_sim["dtr"] = ds_sim["dtr"].where(
            ~(
                (ds_sim.lat == 63.75)
                & (ds_sim.lon == 313.125)
                & (ds_sim.time == ds_sim.time.sel(time="1984-01-10").values)
            )
        )

    # clean up time
    ds_sim["time"] = ds_sim.time.dt.floor("D")

    if "mask" not in ds_sim and "create_mask" in config["extraction"]["simulation"]:
        ds_sim["mask"] = xs.regrid.create_mask(
            dict_sim["fx"], **config["extraction"]["simulation"]["create_mask"]
        )

    ds_sim = xs.clean_up(ds_sim, **config["extraction"]["clean_up"])

    ds_sim = ds_sim.chunk(config["chunks"]["pre-regrid"])

    # save to zarr
    xs.save_to_zarr(ds_sim, output["extract"], **config["save_to_zarr"])
