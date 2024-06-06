from dask.distributed import Client
from dask import config as dskconf
import atexit
import xscen as xs
import logging
from xscen import CONFIG
from utils import save_and_update, save_move_update
from pathlib import Path
from xclim.core.calendar import convert_calendar
import sys

# logging
sys.stderr = open(snakemake.log[0], "w")

xs.load_config('/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/template_paths.yml', '/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/config_ESPO-G_E5L.yml', verbose=(__name__ == '__main__'), reset=True)
logger = logging.getLogger('xscen')

exec_wdir = Path(CONFIG['paths']['exec_workdir'])
regriddir = Path(CONFIG['paths']['regriddir'])
refdir = Path(CONFIG['paths']['refdir'])

ref_source = CONFIG['extraction']['ref_source']

pcat = xs.ProjectCatalog(CONFIG['paths']['project_catalog'], create=True)

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    for region_name, region_dict in CONFIG['custom']['regions'].items():
        if (
                "makeref" in CONFIG["tasks"]
                and not pcat.exists_in_cat(domain=region_name, processing_level='nancount', source=ref_source)
        ):

            with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
                # ds_ref = xr.open_dataset(snakemake.input[0])
                ds_ref = pcat.search(source=ref_source, calendar='default', domain=region_name).to_dask()

                # convert calendars
                ds_refnl = convert_calendar(ds_ref, "noleap")
                save_move_update(ds_refnl, snakemake.output[0])
