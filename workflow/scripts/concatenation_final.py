from dask import config as dskconf
import xarray as xr
import logging
from dask.diagnostics import ProgressBar
import xscen as xs
from xclim.core.calendar import get_calendar
from xscen import (save_to_zarr, CONFIG)


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    fmtkws = {'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    dskconf.set(num_workers=12)
    ProgressBar().register()

    logger.info(f'Contenating {snakemake.wildcards.sim_id} final.')

    list_dsR = []
    for files in range(len(snakemake.input.final)):
        dsR = xr.open_zarr(snakemake.input.final[files])
        dsR.lat.encoding.pop('chunks', None)
        dsR.lon.encoding.pop('chunks', None)
        list_dsR.append(dsR)

    if 'rlat' in dsR:
        dsC = xr.concat(list_dsR, 'rlat')
    else:
        dsC = xr.concat(list_dsR, 'lat')

    dsC.attrs['cat:domain'] = CONFIG['custom']['amno_region']['name']
    dsC.attrs.pop('intake_esm_dataset_key')

    dsC.attrs.pop('cat:path')

    if get_calendar(dsC.time) == '360_day':
        dsC = dsC.chunk({'time': 1440} | CONFIG['custom']['rechunk'])
    else:
        dsC = dsC.chunk({'time': 1460} | CONFIG['custom']['rechunk'])

    save_to_zarr(ds=dsC,
                 filename=str(snakemake.output[0]),
                 mode='o')

    logger.info('Concatenation done.')
