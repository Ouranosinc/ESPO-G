import xscen as xs
import logging
from xscen import CONFIG
import xarray as xr

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':

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

