from dask.distributed import Client
from dask import config as dskconf
import atexit
import xarray as xr
import xscen as xs
import logging
from xscen import (
    CONFIG,
    send_mail_on_exit)



xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')



if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    #atexit.register(send_mail_on_exit, subject=CONFIG['scripting']['subject'])


    with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
        logger.info("debut open_dataset")
        ds_ref = xr.open_zarr(snakemake.input[0])
        logger.info("fin open_dataset")
        # drop to make faster
        dref_ref = ds_ref.drop_vars('dtr')
        dref_ref = dref_ref.chunk(CONFIG['extraction']['reference']['chunks'])
        prop, _ = xs.properties_and_measures(
            ds=dref_ref,
            **CONFIG['extraction']['reference']['properties_and_measures'])
        prop = prop.chunk(CONFIG['custom']['rechunk'])


        xs.save_to_zarr(prop, snakemake.output[0])