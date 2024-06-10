from dask.distributed import Client
from dask import config as dskconf
import atexit
import xscen as xs
import logging
from xscen import CONFIG
from xclim.core.calendar import convert_calendar
import sys
import xarray as xr

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    #atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])
    with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):

        # ds_ref = pcat.search(source=ref_source, calendar='default', domain=region_name).to_dask()

        ds_ref = xr.open_zarr(snakemake.input[0])
        ds_ref360 = convert_calendar(ds_ref, "360_day", align_on="year")


        xs.save_to_zarr(ds_ref360, str(snakemake.output[0]))