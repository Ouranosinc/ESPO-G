from dask.distributed import Client
from dask import config as dskconf
import atexit
import xscen as xs
import logging
from xscen import CONFIG
import sys

# logging
# pas sur pourquoi tu mets ça et ça me donne une erreur alors je l'enleve temporairement
#sys.stderr = open(snakemake.log[0], "w")

# you've put all everything in config, so you can just call that
#xs.load_config('/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/template_paths.yml', '/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/config_ESPO-G_E5L.yml', verbose=(__name__ == '__main__'), reset=True)
import os
xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')


if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    # not necessary for each task
    #atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    # default
    for region_name, region_dict in CONFIG['custom']['regions'].items():
        if region_name == snakemake.wildcards.region:
            with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
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