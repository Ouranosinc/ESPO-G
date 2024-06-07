from dask.distributed import Client
from dask import config as dskconf
import atexit
import xscen as xs
import logging
from xscen import CONFIG
from xclim.core.calendar import convert_calendar
import sys
import xarray as xr

# logging
# sys.stderr = open(snakemake.log[0], "w")
xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
        ds_ref = xr.open_zarr(snakemake.input[0])
        # ds_ref = pcat.search(source=ref_source, calendar='default', domain=region_name).to_dask()

        # convert calendars
        ds_refnl = convert_calendar(ds_ref, "noleap")
        xs.save_to_zarr(ds_refnl, str(snakemake.output[0]))
