"""Flip tasmax and tasmin when there is a temperature inversion."""

from copy import deepcopy

import xarray as xr
import xscen as xs


xr.set_options(keep_attrs=True)

if 1 == 0:  # trick vscode
    import snakemake


if __name__ == "__main__":
    # Get Snakemake parameters
    inputs = snakemake.input
    output = snakemake.output
    config = deepcopy(snakemake.config)

    ds_tasmax = xr.open_zarr(inputs["tasmax"], decode_timedelta=False)
    ds_tasmin = xr.open_zarr(inputs["tasmin"], decode_timedelta=False)

    oldtasmax = ds_tasmax.copy()
    oldtasmin = ds_tasmin.copy()

    # Find where no inversion
    valid_mask = ds_tasmax.tasmax >= ds_tasmin.tasmin

    ds_tasmax["tasmax"] = ds_tasmax.tasmax.where(
        valid_mask.compute(), other=oldtasmin.tasmin
    )

    ds_tasmin["tasmin"] = ds_tasmin.tasmin.where(
        valid_mask.compute(), other=oldtasmax.tasmax
    )

    xs.save_to_zarr(
        ds_tasmin,
        output.tasmin,
        **config["save_to_zarr"],
    )

    xs.save_to_zarr(
        ds_tasmax,
        output.tasmax,
        **config["save_to_zarr"],
    )

    ds_pr = xr.open_zarr(inputs["pr"], decode_timedelta=False)
    #ds_dtr = xr.open_zarr(inputs["dtr"], decode_timedelta=False)

    xs.save_to_zarr(
        ds_pr,
        output.pr,
        **config["save_to_zarr"],
    )

    # xs.save_to_zarr(
    #     ds_dtr,
    #     output.dtr,
    #     **config["save_to_zarr"],
    # )
