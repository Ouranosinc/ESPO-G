from dask.distributed import Client
from dask import config as dskconf
import logging
import xscen as xs
from xscen import (search_data_catalogs,
    extract_dataset,
    CONFIG,measure_time, timeout, clean_up)


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    #atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])


    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)


    with (
        Client(n_workers=2, threads_per_worker=3, memory_limit="30GB", **daskkws),
        measure_time(name=f'cleanup', logger=logger),
        timeout(18000, task='clean_up')
    ):
        # get all adjusted data
        cat = search_data_catalogs(**CONFIG['clean_up']['search_data_catalogs'],
                                   other_search_criteria={'id': [snakemake.wildcards.sim_id],
                                                          'processing_level': ["biasadjusted"],
                                                          'domain': snakemake.wildcards.region}
                                   )
        dc = cat.popitem()[1]
        ds = extract_dataset(catalog=dc,
                             periods=CONFIG['custom']['sim_period']
                             )['D']

        ds = clean_up(ds=ds,
                      **CONFIG['clean_up']['xscen_clean_up']
                      )

        # fix the problematic data
        if snakemake.wildcards.sim_id in CONFIG['clean_up']['problems']:
            logger.info('Mask grid cells where tasmin < 100 K.')
            ds = ds.where(ds.tasmin > 100)

        xs.save_to_zarr(ds, str(snakemake.output[0]), itervar=True)
