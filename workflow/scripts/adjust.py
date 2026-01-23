from copy import deepcopy
import xarray as xr
import xscen as xs
import xclim as xc
import xsdba as xa
import numpy as np
from workflow.scripts.utils import dask_cluster, save
import datetime
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    var = snakemake.wildcards.var
    input_train = snakemake.input.train
    input_rechunk = snakemake.input.rechunk
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)

    client=dask_cluster(snakemake.params, config['dask']['client'])

    # load sim ds
    ds_sim = xr.open_zarr(input_rechunk, decode_timedelta=False)
    ds_tr = xr.open_zarr(input_train, decode_timedelta=False)

    if 'hursmin' in ds_sim:
        # trick for biasadjustement of hursmin (sim) on hursTasmax (ref)
        ds_sim = ds_sim.rename({'hursmin': 'hursTasmax'})
        #needed until we can use numpy>2, useful for clip in additive transform
        #ds_sim['hursTasmax'] = ds_sim['hursTasmax'].astype(float)
        #ds_sim['hurs'] = ds_sim['hurs'].astype(float)

    #clip before
    #ds_sim['hurs'] = ds_sim['hurs'].clip(0,100)
    #ds_sim['hursTasmax'] = ds_sim['hursTasmax'].clip(0,100)

    # there are some negative dtr in the data (GFDL-ESM4). This puts is back to a very small positive.
    if 'dtr' in ds_sim:
        ds_sim['dtr'] = xa.processing.jitter_under_thresh(ds_sim.dtr, "1e-4 K")

    # adjust
    ds_scen = xs.adjust(
        dsim=ds_sim,
        dtrain=ds_tr,
        **config['biasadjust']['variables'][var]['adjusting_args']
        )

    # until xscen>=0.13.1,   final clip here instead of with xscen.clean_up
    # new_history = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Clipped to [0,100]"
    # if 'hurs' in ds_scen:
    #     ds_scen['hurs'] = ds_scen['hurs'].clip(0,100)
    #     ds_scen['hurs'].attrs['history'] = ds_scen['hurs'].attrs.get('history', '') + new_history
    # if 'hursTasmax' in ds_scen:
    #     ds_scen['hursTasmax'] = ds_scen['hursTasmax'].clip(0,100)
    #     ds_scen['hursTasmax'].attrs['history'] = ds_scen['hursTasmax'].attrs.get('history', '') + new_history


    xs.save_to_zarr(ds_scen, output, **config['save_to_zarr'], rechunk=config['chunks']['workingloc'])
