from dask.distributed import Client
from dask import config as dskconf
import atexit
import xscen as xs
import logging
from xscen import CONFIG
from xclim.core.calendar import convert_calendar
import sys
import xarray as xr

# logging
sys.stderr = open(snakemake.log[0], "w")

xs.load_config('/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/template_paths.yml', '/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/config_ESPO-G_E5L.yml', verbose=(__name__ == '__main__'), reset=True)
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
        ds_ref = xr.open_dataset(snakemake.input[0]).to_dask()
        # ds_ref = pcat.search(source=ref_source, calendar='default', domain=region_name).to_dask()

        # convert calendars
        ds_refnl = convert_calendar(ds_ref, "noleap")
        xs.save_to_zarr(ds_refnl, str(snakemake.output[0]))