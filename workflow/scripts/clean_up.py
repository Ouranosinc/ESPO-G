import xscen as xs
import xarray as xr
from xscen import CONFIG
import numpy as np
xr.set_options(keep_attrs=True)
from workflow.scripts.utils import dask_cluster
from xscen.xclim_modules import conversions

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)
    
    # get all adjusted data
    ds = xr.open_mfdataset(snakemake.input, engine='zarr', decode_timedelta=False)
    ds = ds.assign(tasmin=conversions.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax))
    ds = ds.drop_vars('dtr')

    ds = xs.clean_up(ds=ds,**CONFIG['clean_up']['xscen_clean_up'])

    # fix the problematic data
    if snakemake.wildcards.sim_id in CONFIG['clean_up']['problems']:
        ds = ds.where(ds.tasmin > 100)

    xs.save_to_zarr(ds, snakemake.output[0], itervar=True)
