from dask.distributed import Client, LocalCluster
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

    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads_per_worker,
                           memory_limit=snakemake.params.memory_limit, **daskkws)
    client = Client(cluster)

    ds_ref = xr.open_zarr(snakemake.input[0])
    ds_ref360 = convert_calendar(ds_ref, "360_day", align_on="year")


    xs.save_to_zarr(ds_ref360, str(snakemake.output[0]))