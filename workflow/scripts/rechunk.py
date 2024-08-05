import os
from dask.distributed import Client, LocalCluster
from dask import config as dskconf
import xarray as xr
import logging
import tempfile
import shutil
import xscen as xs
from xscen.io import rechunk
from xscen import (CONFIG, measure_time, timeout)
xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    #atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

#  ---RECHUNK---
    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads_per_worker,
               memory_limit=snakemake.params.memory_limit, **daskkws)
    client = Client(cluster)
    with (
            measure_time(name=f'rechunk', logger=logger),
            timeout(18000, task='rechunk')
    ):
        #rechunk in exec
        specific_temp_dir = CONFIG["io"]["rechunk"]["temp_store"]
        os.makedirs(specific_temp_dir, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=specific_temp_dir, prefix=f"{snakemake.wildcards.sim_id}_{snakemake.wildcards.region}_")

        rechunk(path_in=str(snakemake.input[0]),
                path_out=str(snakemake.output[0]),
                chunks_over_dim=CONFIG['custom']['chunks'],
                temp_store=temp_dir,
                overwrite=True)
