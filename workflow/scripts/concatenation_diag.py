from dask import config as dskconf
import xarray as xr
import logging
from dask.diagnostics import ProgressBar
import xscen as xs
from xscen import (save_to_zarr, CONFIG)


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})


    fmtkws = {'level': snakemake.wildcards.level, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    dskconf.set(num_workers=12)
    ProgressBar().register()

    logger.info(f'Contenating {snakemake.wildcards.sim_id} {snakemake.wildcards.level}.')

    list_dsR = []
    for files in range(len(snakemake.input.diag_meas_prop)):
        dsR =  xr.open_zarr(snakemake.input.diag_meas_prop[files])
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

    dsC = dsC.chunk(CONFIG['custom']['rechunk'])

    save_to_zarr(ds=dsC,
                 filename=str(snakemake.output[0]),
                 mode='o')

    logger.info('Concatenation done.')