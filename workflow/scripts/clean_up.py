import xscen as xs
import xarray as xr
from xscen import CONFIG
import numpy as np
import datetime
xr.set_options(keep_attrs=True)
from workflow.scripts.utils import dask_cluster
from xscen.xclim_modules import conversions
from pathlib import Path
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

if __name__ == '__main__':
    
    # get all adjusted data
    ds = xr.open_mfdataset(snakemake.input.sim, engine='zarr', decode_timedelta=False)

    conv_mod= xs.indicators.load_xclim_module(Path(conversions.__file__).with_suffix(""))
    ds = ds.assign(tasmin=conv_mod.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax))

    
    # fill holes
    # load ref
    # choose right calendar
    simcal = xc.core.calendar.get_calendar(ds_hist)
    refcal = xs.utils.minimum_calendar(simcal, 'noleap')
    # snakemake can't have 360_day as a keyword..
    input_cal = 'noleap' if refcal == 'noleap' else  'day360' if refcal == '360_day' else 'unknown'
    ds_ref = xr.open_zarr(getattr(snakemake.input, input_cal), decode_timedelta=False)
    #FIXME: until this is in xscen
    # check if any non-time dimension are different
    if (np.array([ds.sizes[d] != fill_nan_ds.sizes[d] 
                    for d in ds.dims if d !='time']).any())  or (
                        ds.attrs.get('cat:domain', 'foo') != fill_nan_ds.attrs.get('cat:domain', 'foo') ):
        raise ValueError(
        "The non-time dimensions or the cat:domain attribute of the simulation"
        " and reference datasets do not match. "
        "Cannot fill missing values."
    )
    for var in ds.data_vars:
        if var in fill_nan_ds:
            ds[var]=ds[var].combine_first(fill_nan_ds[var])
            
            new_history = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Filled missing values using {fill_nan_ds.get('cat:id','')} dataset."
            history = f"{new_history}\n{ds[var].attrs['history']}" if "history" in ds[var].attrs else new_history
            ds[var].attrs["history"] = history

    # clean up
    ds = xs.clean_up(ds=ds,**CONFIG['clean_up']['xscen_clean_up'])

    ds.attrs['cat:_data_format_'] = 'zarr'
    ds.attrs['cat:date'] = 'zarr'


    chunks=xs.utils.translate_time_chunk(
        CONFIG['chunks']['final'],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,)
    ds=ds.chunk(chunks)

    xs.save_to_zarr(ds, snakemake.output[0], itervar=True, **CONFIG['clean_up']['save'])
