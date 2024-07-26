from dask.distributed import Client, LocalCluster
from dask import config as dskconf
import logging
import xscen as xs
from xscen import (
    extract_dataset,
    CONFIG,
    measure_time, timeout
)

import subprocess
subprocess.call(['sh', 'espo_snakemake.sh'])

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads,
                           memory_limit="25GB", **daskkws)
    client = Client(cluster)

    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    # ---EXTRACT---

    with (client,
         measure_time(name='extract', logger=logger),
         timeout(18000, task='extract')
    ):
        logger.info('Adding config to log file')
        f1 = open(CONFIG['logging']['handlers']['file']['filename'], 'a+')
        f2 = open('config/config.yaml', 'r')
        f1.write(f2.read())
        f1.close()
        f2.close()
        cat_sim_id = xs.search_data_catalogs(data_catalogs=CONFIG['paths']['cat_sim'],
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
        ds_sim.attrs["cat:_data_format_"] = 'zarr'
        # save to zarr
        xs.save_to_zarr(ds_sim, str(snakemake.output[0]))
