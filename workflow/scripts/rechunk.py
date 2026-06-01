"""Chunk the data for bias adjustment."""

from copy import deepcopy

import xarray as xr
import xscen as xs

from workflow.scripts.utils import dask_cluster


if 1 == 0:  # trick vscode
    import snakemake


if __name__ == "__main__":
    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs = snakemake.input
    output = snakemake.output[0]

    client = dask_cluster(snakemake.params, config["dask"]["client"])

    # Try to not use this
    # xs.io.rechunk(
    #     path_in=str(snakemake.input[0]),
    #     path_out=f"{os.environ['SLURM_TMPDIR']}/rechunked+{snakemake.wildcards.sim_id}+{snakemake.wildcards.subregion}/",
    #     chunks_over_dim={
    #         k: v for k, v in config["chunks"]["working"].items() if k in ["time", "loc"]
    #     },
    #     temp_store=f"{os.environ['SLURM_TMPDIR']}/{snakemake.wildcards.sim_id}+{snakemake.wildcards.subregion}/",
    #     overwrite=True,
    # )  # explicit parse_config magic if you uncomment this

    # # test to get rif of rechunker
    ds = xr.open_zarr(inputs[0], decode_timedelta=False)
    ds = xs.io.rechunk_for_saving(ds, rechunk=config["chunks"]["workingloc"])

    # patch holes
    # ffill for the last time step.
    # bbfill for the first time step.
    ds["tasmax"] = ds["tasmax"].interpolate_na("time", method="linear").ffill("time")
    ds["tasmin"] = (
        ds["tasmin"].interpolate_na("time", method="linear").ffill("time").bfill("time")
    )
    ds["dtr"] = (
        ds["dtr"].interpolate_na("time", method="linear").ffill("time").bfill("time")
    )
    ds["pr"] = ds["pr"].where(ds["pr"].notnull(), other=0)

    # fix encoding chunks issue
    for var in ds.data_vars:
        if "chunks" in ds[var].encoding:
            del ds[var].encoding["chunks"]

    #TODO: tmp, put this in extract
    #ds = ds.expand_dims(realization=[ds.attrs['cat:id']])

    xs.save_to_zarr(ds, output, **config["save_to_zarr"])
