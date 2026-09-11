"""Flip tasmax and tasmin when there is a temperature inversion."""

from copy import deepcopy
from datetime import datetime
from pathlib import Path

import xarray as xr
import xscen as xs
from xscen.xclim_modules import conversions


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

    # keep a trace of pre-swap dtr
    conv_mod = xs.indicators.load_xclim_module(
        Path(conversions.__file__).with_suffix("")
    )
    ds_dtr = conv_mod.dtr(tasmin=ds_tasmin.tasmin, tasmax=ds_tasmax.tasmax).to_dataset(
        name="dtr"
    )
    ds_dtr.attrs = ds_tasmax.attrs
    ds_dtr["dtr"].attrs["history"] = (
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] dtr computed from adjusted tasmax and \
        adjusted tasmin before the swap.\n"
    ) + ds_dtr["dtr"].attrs["history"]

    xs.save_to_zarr(
        ds_dtr,
        output.dtrpreswap,
        **config["save_to_zarr"],
    )

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
