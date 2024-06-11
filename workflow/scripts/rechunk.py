from dask.distributed import Client
from dask import config as dskconf
import xarray as xr
import logging
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
    with (
            Client(n_workers=2, threads_per_worker=5, memory_limit="18GB", **daskkws),
            measure_time(name=f'rechunk', logger=logger),
            timeout(18000, task='rechunk')
    ):
        #rechunk in exec
        rechunk(path_in=snakemake.input[0],
                path_out=snakemake.output[0],
                chunks_over_dim=CONFIG['custom']['chunks'],
                overwrite=True)


        ds_sim_rechunked = xr.open_zarr(str(snakemake.output[0]), decode_timedelta=False)
        xs.save_to_zarr(ds_sim_rechunked, str(snakemake.output[0]))
