from copy import deepcopy
import xscen as xs
import xclim as xc
import xarray as xr
import numpy as np
from datetime import datetime
xr.set_options(keep_attrs=True)
from workflow.scripts.utils import dask_cluster, save
from xscen.xclim_modules import conversions
from pathlib import Path
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    coords = snakemake.input[0]
    inputs = snakemake.input #TODO: check why gab but [1:]
    input_noleap = snakemake.input.noleap
    input_360_day = snakemake.input.day360
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)
    
    # get all adjusted data
    ds = xr.open_mfdataset(inputs['sim'], engine='zarr', decode_timedelta=False)

    # calculate tasmin back
    conv_mod= xs.indicators.load_xclim_module(Path(conversions.__file__).with_suffix(""))
    ds = ds.assign(tasmin=conv_mod.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax))
    ds['tasmin'].attrs['history'] = (f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Tasmin computed from tasmax and dtr.\n") + ds['tasmin'].attrs['history'] 

    
    # fill holes
    # load ref
    # choose right calendar
    # refcal = xs.utils.minimum_calendar(ds.time.dt.calendar, 'noleap')
    # # snakemake can't have 360_day as a keyword..
    # input_cal = input_noleap if refcal == 'noleap' else  input_360_day if refcal == '360_day' else 'unknown'
    # fill_nan_ds = xr.open_zarr(input_cal, decode_timedelta=False)
    
    #  until this is in xscen
    # # check if any non-time dimension are different
    # if (np.array([ds.sizes[d] != fill_nan_ds.sizes[d] 
    #                 for d in ds.dims if d !='time']).any())  or (
    #                     ds.attrs.get('cat:domain', 'foo') != fill_nan_ds.attrs.get('cat:domain', 'foo') ):
    #     raise ValueError(
    #     "The non-time dimensions or the cat:domain attribute of the simulation"
    #     " and reference datasets do not match. "
    #     "Cannot fill missing values."
    # )
    # for var in ds.data_vars:
    #     if var in fill_nan_ds:
    #         ds[var]=ds[var].combine_first(fill_nan_ds[var])
            
    #         new_history = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Filled missing values using {fill_nan_ds.get('cat:id','')} dataset."
    #         history = f"{new_history}\n{ds[var].attrs['history']}" if "history" in ds[var].attrs else new_history
    #         ds[var].attrs["history"] = history

    # clean up
    ds = xs.clean_up(ds=ds,**config['clean_up']['xscen_clean_up'])

    ds.attrs['cat:_data_format_'] = 'zarr'
    ds.attrs['cat:date'] = 'zarr'


    chunks=xs.utils.translate_time_chunk(
        config['chunks']['final'],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,)
    ds=ds.chunk(chunks)

    save(ds, output, itervar=True, **config['clean_up']['save'])
