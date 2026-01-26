from copy import deepcopy
import xarray as xr
import xscen as xs
import xclim as xc
import numpy as np
from workflow.scripts.utils import dask_cluster
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    var = snakemake.wildcards.var
    input_noleap = snakemake.input.noleap
    input_360_day = snakemake.input.day360
    input_rechunk = snakemake.input.rechunk
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)

    client=dask_cluster(snakemake.params, config['dask']['client'])

    # load hist ds (simulation)
    ds_hist = xr.open_zarr(input_rechunk , decode_timedelta=False)
    
    if 'hursmin' in ds_hist:
        # trick for biasadjustement of hursmin (sim) on hursTasmax (ref)
        ds_hist = ds_hist.rename({'hursmin': 'hursTasmax'})

        # needed until we can use numpy>2, for clip in additive transform
        # ds_hist['hursTasmax'] = ds_hist['hursTasmax'].astype(float)
        # ds_hist['hurs'] = ds_hist['hurs'].astype(float)

    # load ref ds
    # choose right calendar
    simcal = xc.core.calendar.get_calendar(ds_hist)
    refcal = xs.utils.minimum_calendar(simcal, 'noleap')

    # snakemake can't have 360_day as a keyword..
    input_cal = input_noleap if refcal == 'noleap' else  input_360_day if refcal == '360_day' else 'unknown'
    ds_ref = xr.open_zarr(input_cal, decode_timedelta=False)

    #clip tmp
    # ds_ref['hurs'] = ds_ref['hurs'].clip(0,100)
    # ds_hist['hurs'] = ds_hist['hurs'].clip(0,100)
    # ds_ref['hursTasmax'] = ds_ref['hursTasmax'].clip(0,100)
    # ds_hist['hursTasmax'] = ds_hist['hursTasmax'].clip(0,100)
    #blba

    # training
    ds_tr = xs.train(
        dref=ds_ref,
        dhist=ds_hist,
        var=[var],
        **config['biasadjust']['variables'][var]['training_args']
        )

    # Add attribute for reference
    ds_tr.attrs['cat:bias_adjust_reference'] = f"{ds_ref.attrs.get('cat:source', 'unknown')}{ds_ref.attrs.get('cat:version', '')}"

    
    for v in ['lat','lon']:
        del ds_tr[v].encoding['chunks']

    xs.save_to_zarr(ds_tr, output, **config['save_to_zarr'], rechunk=config['chunks']['workingloc'])

