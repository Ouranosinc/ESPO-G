"""Adjustment"""

from copy import deepcopy

import xarray as xr
import xscen as xs
import xsdba as xa

from workflow.scripts.utils import dask_cluster


if 1 == 0:  # trick vscode
    import snakemake


if __name__ == "__main__":
    # Get Snakemake parameters
    var = snakemake.wildcards.var
    sim_id = snakemake.wildcards.sim_id
    input_train = snakemake.input.train
    input_rechunk = snakemake.input.rechunk
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)
    print(input_rechunk)
    print(output)

    client = dask_cluster(snakemake.params, config["dask"]["client"])

    # load sim ds
    ds_sim = xr.open_mfdataset(
        input_rechunk,
        engine='zarr',
        concat_dim='realization',
        combine='nested',
        decode_timedelta=False
    )
    ds_sim = ds_sim.chunk({"realization": -1})
    print(ds_sim)

    ds_tr = xr.open_zarr(input_train, decode_timedelta=False)

    if "hursmin" in ds_sim:
        # trick for biasadjustement of hursmin (sim) on hursTasmax (ref)
        ds_sim = ds_sim.rename({"hursmin": "hursTasmax"})
        # needed until we can use numpy>2, useful for clip in additive transform
        # ds_sim['hursTasmax'] = ds_sim['hursTasmax'].astype(float)
        # ds_sim['hurs'] = ds_sim['hurs'].astype(float)

    # clip before
    # ds_sim['hurs'] = ds_sim['hurs'].clip(0,100)
    # ds_sim['hursTasmax'] = ds_sim['hursTasmax'].clip(0,100)

    # there are some negative dtr in the data (GFDL-ESM4).
    # This puts is back to a very small positive.
    if "dtr" in ds_sim:
        ds_sim["dtr"] = xa.processing.jitter_under_thresh(ds_sim.dtr, "1e-4 K")

    # adjust
    ds_scen = xs.adjust(
        dsim=ds_sim,
        dtrain=ds_tr,
        **config["biasadjust"]["variables"][var]["adjusting_args"],
    )

    out = ds_scen.sel(realization=sim_id)
    print(out)
    out['realization'] = out['realization'].astype('str')
    print(out)
    xs.save_to_zarr(
        out,
        output,
        **config["save_to_zarr"],
        rechunk=config["chunks"]["workingloc"],
    )
