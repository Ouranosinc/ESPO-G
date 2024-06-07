from dask.distributed import Client
from dask import config as dskconf
import atexit
import xarray as xr
import xscen as xs
import logging
from pathlib import Path
from xscen import (
    CONFIG,
    send_mail_on_exit)
import sys

exec_wdir = Path(CONFIG['paths']['exec_workdir'])
# Load configuration
xs.load_config('/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/template_paths.yml', '/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/config_ESPO-G_E5L.yml', verbose=(__name__ == '__main__'), reset=True)
logger = logging.getLogger('xscen')

# logging
sys.stderr = open(snakemake.log[0], "w")


if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    atexit.register(send_mail_on_exit, subject=CONFIG['scripting']['subject'])


    with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
        logger.info("debut open_dataset")
        ds_ref = xr.open_dataset(snakemake.input[0]).to_dask()
        logger.info("fin open_dataset")
        # drop to make faster
        dref_ref = ds_ref.drop_vars('dtr')
        dref_ref = dref_ref.chunk(CONFIG['extraction']['reference']['chunks'])
        prop, _ = xs.properties_and_measures(
            ds=dref_ref,
            **CONFIG['extraction']['reference']['properties_and_measures'])
        prop = prop.chunk(CONFIG['custom']['rechunk'])
        path_diag = snakemake.output[0]
        path_diag_exec = f"{exec_wdir}/{path_diag.name}"


        xs.save_to_zarr(prop, snakemake.output[0])


