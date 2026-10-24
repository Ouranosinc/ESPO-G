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

    xs.save_to_zarr(ds, output, **config["save_to_zarr"])
