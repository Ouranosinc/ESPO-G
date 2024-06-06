from dask.distributed import Client
from dask import config as dskconf
import atexit
import xscen as xs
import logging
from xscen import CONFIG
from utils import save_and_update, save_move_update
from pathlib import Path
import sys

# logging
sys.stderr = open(snakemake.log[0], "w")

xs.load_config('/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/template_paths.yml', '/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/config_ESPO-G_E5L.yml', verbose=(__name__ == '__main__'), reset=True)
logger = logging.getLogger('xscen')

exec_wdir = Path(CONFIG['paths']['exec_workdir'])
regriddir = Path(CONFIG['paths']['regriddir'])
refdir = Path(CONFIG['paths']['refdir'])

ref_source = CONFIG['extraction']['ref_source']


if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    # default

    with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
        # search
        cat_ref = xs.search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

        # extract
        dc = cat_ref.popitem()[1]
        ds_ref = xs.extract_dataset(catalog=dc,
                                    region=CONFIG['custom']['regions'][{snakemake.wildcards.region}],
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


        xs.save_to_zarr(ds_ref, snakemake.output[0])