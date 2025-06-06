import xscen as xs
import xarray as xr
from xscen import CONFIG
import numpy as np
xr.set_options(keep_attrs=True)
from workflow.scripts.utils import dask_cluster
from xscen.xclim_modules import conversions
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

if __name__ == '__main__':

    #client=dask_cluster(snakemake.params)
    
    # get all adjusted data
    ds = xr.open_mfdataset(snakemake.input, engine='zarr', decode_timedelta=False)
    ds = ds.assign(tasmin=conversions.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax))
    #ds = ds.drop_vars('dtr')

    ds = xs.clean_up(ds=ds,**CONFIG['clean_up']['xscen_clean_up'])

    ds.attrs['cat:_data_format_'] = 'zarr'
    ds.attrs['cat:date'] = 'zarr'

    # fix the problematic data
    if snakemake.wildcards.sim_id in CONFIG['clean_up']['problems']:
        ds = ds.where(ds.tasmin > 100)

    chunks=xs.utils.translate_time_chunk(
        CONFIG['chunks']['final'],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,)
    ds=ds.chunk(chunks)

    xs.save_to_zarr(ds, snakemake.output[0], itervar=True, **CONFIG['clean_up']['save'])
