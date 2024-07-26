from dask.distributed import Client, LocalCluster
from dask_jobqueue import SLURMCluster
from dask import config as dskconf
import atexit
import xscen as xs
import logging
from xscen import CONFIG
import sys
import os

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask']['client']
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads,
               memory_limit="25GB", **daskkws)
    client = Client(cluster)

    with (client):
        # default
        for region_name, region_dict in CONFIG['custom']['regions'].items():
            if region_name == snakemake.wildcards.region:
                # search
                cat_ref = xs.search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

                # extract
                dc = cat_ref.popitem()[1]
                ds_ref = xs.extract_dataset(catalog=dc,
                                            region=region_dict,
                                            **CONFIG['extraction']['reference']['extract_dataset']
                                            )['D']

                # stack
                if CONFIG['custom']['stack_drop_nans']:
                    var = list(ds_ref.data_vars)[0]
                    ds_ref = xs.utils.stack_drop_nans(
                        ds_ref,
                        ds_ref[var].isel(time=0, drop=True).notnull().compute(),
                    )
                # chunk
                ds_ref = ds_ref.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_ref.dims})

                xs.save_to_zarr(ds_ref, str(snakemake.output[0]))