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
# sys.stderr = open(snakemake.log[0], "w")

# xs.load_config('/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/template_paths.yml', '/home/ocisse/ESPO-G-stage-snakemake/ESPO-G-stage-snakemake/configuration/config_ESPO-G_E5L.yml', verbose=(__name__ == '__main__'), reset=True)
xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    # atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
        # concat
        logger.info(f'Contenating diag-ref-prop.')
        list_dsR = []
        for file in snakemake.input.diag:
            dsR = xr.open_dataset(file)
            list_dsR.append(dsR)
        if 'rlat' in dsR:
            dsC = xr.concat(list_dsR, 'rlat')
        else:
            dsC = xr.concat(list_dsR, 'lat')

        dsC.attrs['cat:domain'] = CONFIG['custom']['amno_region']['name']

        for var in dsC.data_vars:
            dsC[var].encoding.pop('chunks', None)
        dsC = dsC.chunk(CONFIG['custom']['rechunk'])

        xs.save_to_zarr(dsC, str(snakemake.output[0]), mode='o')

