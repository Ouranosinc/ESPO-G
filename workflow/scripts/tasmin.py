"""Create tasmin from tasmax and dtr."""

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
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)

    ds = xr.open_mfdataset(inputs, engine="zarr", decode_timedelta=False)

    # calculate tasmin back
    conv_mod = xs.indicators.load_xclim_module(
        Path(conversions.__file__).with_suffix("")
    )
    ds = ds.assign(tasmin=conv_mod.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax))
    ds["tasmin"].attrs["history"] = (
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Tasmin computed from tasmax and dtr.\n"
    ) + ds["tasmin"].attrs["history"]
    ds = ds.drop_vars(["dtr", "tasmax"])

    ds = xs.clean_up(ds=ds, **config["clean_up"]["xscen_clean_up"]["tasmin"])

    chunks = xs.utils.translate_time_chunk(
        config["chunks"]["final"],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,
    )

    xs.save_to_zarr(ds, output, **config["save_to_zarr"], rechunk=chunks)
