from dask.distributed import Client, LocalCluster
from dask import config as dskconf
import logging
import os
import xscen as xs
from xscen import CONFIG


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')


if __name__ == '__main__':
    
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'}) # for array.slicing.split_large_chunks
    cluster = LocalCluster(
        n_workers=snakemake.params.n_workers,
        threads_per_worker=snakemake.params.cpus_per_task/snakemake.params.n_workers,
        memory_limit=f"{int(int(snakemake.params.mem.replace('GB',''))/snakemake.params.n_workers)}GB",
        local_directory=os.environ['SLURM_TMPDIR'], **CONFIG['dask'].get('client', {}))
    client = Client(cluster)

    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}

    with (
         xs.measure_time(name='extract', logger=logger),
         xs.timeout(18000, task='extract')
    ):
        cat_sim_id = xs.search_data_catalogs(data_catalogs=CONFIG['paths']['cat_sim'],
                                             variables_and_freqs={'tasmax': 'D', 'tasmin': 'D', 'pr': 'D',
                                                                  'dtr': 'D'},
                                             match_hist_and_fut=True,
                                             allow_conversion=True,
                                             allow_resampling=False,
                                             restrict_members={'ordered': 1},
                                             periods=['1950', '2100'],
                                             other_search_criteria={'id': snakemake.wildcards.sim_id})

        # extract
        dc_id = cat_sim_id.popitem()[1]
        ds_sim = xs.extract_dataset(catalog=dc_id,
                                 region=CONFIG['custom']['amno_region'],
                                 **CONFIG['extraction']['simulation']['extract_dataset'],
                                 )['D']

        ds_sim['time'] = ds_sim.time.dt.floor('D')  # probably this wont be need when data is cleaned

        ds_sim = ds_sim.chunk(CONFIG['extraction']['simulation']['chunks'])
        ds_sim.attrs["cat:_data_format_"] = 'zarr'
        # save to zarr
        xs.save_to_zarr(ds_sim, str(snakemake.output[0]))
