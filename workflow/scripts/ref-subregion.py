"""Divide reference in regions to parallelize the processing."""

from copy import deepcopy

import xarray as xr
import xscen as xs


if 1 == 0:  # trick vscode
    import snakemake


if __name__ == "__main__":
    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs = snakemake.input
    output = snakemake.output
    subregion = snakemake.wildcards.subregion

    ds_ref = xr.open_zarr(inputs[0], decode_timedelta=False)

    # cut region
    n = config["subregions"]["n"]
    r = int(snakemake.wildcards.subregion.replace(f"sr-", ""))
    ds_ref = ds_ref.sel(loc=slice(n * r, n * (r + 1)))

    # chunk
    ds_ref = xs.io.rechunk_for_saving(ds_ref, rechunk=config["chunks"]["workingloc"])

    ds_ref.attrs["cat:calendar"] = "default"
    xs.save_to_zarr(ds_ref, output["default"], **config["save_to_zarr"])

    # noleap
    ds_refnl = ds_ref.convert_calendar("noleap")
    ds_refnl.attrs["cat:calendar"] = "noleap"
    xs.save_to_zarr(ds_refnl, output["noleap"], **config["save_to_zarr"])

    # 360_day
    ds_ref3 = ds_ref.convert_calendar("360_day", align_on="year")
    ds_ref3.attrs["cat:calendar"] = "360_day"
    xs.save_to_zarr(ds_ref3, output["day360"], **config["save_to_zarr"])
