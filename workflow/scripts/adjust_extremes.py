"""Training when using ExtremeValues method."""

from copy import deepcopy

import xarray as xr
import xscen as xs

from workflow.scripts.utils import dask_cluster


if 1 == 0:  # trick vscode
    import snakemake


if __name__ == "__main__":
    # Get Snakemake parameters
    var = snakemake.wildcards.var
    input_train = snakemake.input.train
    input_rechunk = snakemake.input.rechunk
    input_scen = snakemake.input.scen
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)

    # Start Dask cluster
    client = dask_cluster(snakemake.params, config["dask"]["client"])

    # Load sim ds
    ds_sim = xr.open_zarr(input_rechunk, decode_timedelta=False)
    ds_tr = xr.open_zarr(input_train, decode_timedelta=False)
    ds_scen = xr.open_zarr(input_scen, decode_timedelta=False)

    # Add 'scen' to adjusting args
    args = deepcopy(config["biasadjust_extremes"]["variables"][var]["adjusting_args"])
    args["xsdba_adjust_args"] = args.get("xsdba_adjust_args", {})
    args["xsdba_adjust_args"]["scen"] = ds_scen[var]

    # Adjust
    ds_scen = xs.adjust(dsim=ds_sim, dtrain=ds_tr, **args)

    xs.save_to_zarr(
        ds_scen,
        output,
        rechunk=config["chunks"]["workingloc"],
        **config["save_to_zarr"],
    )
