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
    ds = ds.assign(dtr=conv_mod.dtr(tasmin=ds.tasmin, tasmax=ds.tasmax))
    ds["dtr"].attrs["history"] = (
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] dtr computed from tasmax and tasmin.\n"
    ) + ds["dtr"].attrs["history"]
    ds = ds.drop_vars(["tasmin", "tasmax"])

    argsc = config["clean_up"]["xscen_clean_up"]["dtr"].copy()
    del argsc["maybe_unstack_dict"]  # done in concat_clean_up
    ds = xs.clean_up(ds=ds, **argsc)

    chunks = xs.utils.translate_time_chunk(
        config["chunks"]["final"],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,
    )

    xs.save_to_zarr(ds, output, **config["save_to_zarr"], rechunk=chunks)
