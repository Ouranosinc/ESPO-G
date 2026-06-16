"""Regrid simulation on reference grid."""

from copy import deepcopy

import xarray as xr
import xscen as xs


if 1 == 0:  # trick vscode
    import snakemake


if __name__ == "__main__":
    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs = snakemake.input
    output = snakemake.output[0]

    # client=dask_cluster(snakemake.params,config['dask']['client'])

    ds_input = xr.open_zarr(inputs["extract"], decode_timedelta=False)  # .compute()
    ds_input = ds_input.drop_vars("crs", errors="ignore")

    ds_target = xr.open_zarr(inputs["noleap"], decode_timedelta=False).compute()

    ds_regrid = xs.regrid_dataset(
        ds=ds_input, ds_grid=ds_target, **config["regrid"]["regrid_dataset"]
    )

    # save
    xs.save_to_zarr(ds_regrid, output, **config["save_to_zarr"])
