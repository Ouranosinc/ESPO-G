from copy import deepcopy
from pathlib import Path
import xarray as xr
import xscen as xs
import xclim as xc
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
    
    # Start Dask cluster
    client=dask_cluster(snakemake.params, config['dask']['client'])

    # Load ds_hist (simulation)
    ds_hist = xr.open_zarr(input_rechunk, decode_timedelta=False)

    # Load ds_ref
    # Choose the right calendar
    simcal = xc.core.calendar.get_calendar(ds_hist)
    refcal = xs.utils.minimum_calendar(simcal, 'noleap')

    # snakemake can't have 360_day as a keyword..
    input_cal = input_noleap if refcal == 'noleap' else  input_360_day if refcal == '360_day' else 'unknown'
    ds_ref = xr.open_zarr(input_cal, decode_timedelta=False)

    # Training
    ds_tr = xs.train(
        dref=ds_ref,
        dhist=ds_hist,
        var=[var],
        **config['biasadjust_extremes']['variables'][var]['training_args']
        )
    
    xs.save_to_zarr(ds_tr, output, **config['save_to_zarr'], rechunk=config['chunks']['workingloc'])