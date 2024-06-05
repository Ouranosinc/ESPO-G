from dask.distributed import Client
from dask import config as dskconf
import atexit
from xarray import open_dataset
import snakemake
import xscen as xs
import logging
from utils import save_move_update
from pathlib import Path
from xscen import (
    CONFIG,
    send_mail_on_exit)
import sys



# Load configuration
xs.load_config('ESPO-G/configuration/config_ESPO-G_E5L.yml', 'ESPO-G/configuration/template_paths.yml', verbose=(__name__ == '__main__'), reset=True)
logger = logging.getLogger('xscen')

# logging
sys.stderr = open(snakemake.log[0], "w")

ref_source = CONFIG['extraction']['ref_source']
workdir = Path(CONFIG['paths']['workdir'])


if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    atexit.register(send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    path_diag, prop = rule_drop_to_make_faster()
    for outputfile in path_diag:
        with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
                if (not pcat.exists_in_cat(domain=path_diag.values(), processing_level='diag-ref-prop',
                                          source=ref_source)) and ('diagnostics' in CONFIG['tasks']):
                    with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
                        path_diag_exec = f"{workdir}/{path_diag.name}"

                        save_move_update(ds=prop,
                                         pcat=pcat,
                                         init_path=path_diag_exec,
                                         final_path=path_diag.keys(),)


