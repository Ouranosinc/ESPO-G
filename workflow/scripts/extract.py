from dask.distributed import Client
from dask import config as dskconf
import logging
import xscen as xs
from xscen import (
    extract_dataset,
    CONFIG,
    measure_time, timeout
)

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    #atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])


    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    # ---EXTRACT---

    with (
        Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws),
        # Client(n_workers=1, threads_per_worker=5,memory_limit="50GB", **daskkws), # only for CNRM-ESM2-1
        measure_time(name='extract', logger=logger),
        timeout(18000, task='extract')
    ):
        logger.info('Adding config to log file')
        f1 = open(CONFIG['logging_PATH']['handlers']['file']['filename'], 'a+')
        f2 = open('config/config.yaml', 'r')
        f1.write(f2.read())
        f1.close()
        f2.close()
        cat_sim_id = xs.search_data_catalogs(data_catalogs=['/tank/scenario/catalogues/simulation.json'],
                                             variables_and_freqs={'tasmax': 'D', 'tasmin': 'D', 'pr': 'D',
                                                                  'dtr': 'D'},
        match_hist_and_fut = True,
        allow_conversion = True,
        allow_resampling = False,
        restrict_members =
        {'ordered': 1},
        periods = ['1950', '2100'],
        other_search_criteria = {'id': snakemake.wildcards.sim_id})

        # extract
        dc_id = cat_sim_id.popitem()[1]
        ds_sim = extract_dataset(catalog=dc_id,
                                 region=CONFIG['custom']['amno_region'],
                                 **CONFIG['extraction']['simulation']['extract_dataset'],
                                 )['D']

        ds_sim['time'] = ds_sim.time.dt.floor('D')  # probably this wont be need when data is cleaned

        ds_sim = ds_sim.chunk(CONFIG['extraction']['simulation']['chunks'])

        # save to zarr
        xs.save_to_zarr(ds_sim, str(snakemake.output[0]))
