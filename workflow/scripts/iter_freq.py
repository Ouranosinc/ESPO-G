from dask import config as dskconf
import xarray as xr
import logging
from dask.diagnostics import ProgressBar
import xscen as xs
from xscen import CONFIG

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    fmtkws = {'xrfreq': snakemake.wildcards.xrfreq, 'sim_id': snakemake.wildcards.sim_id, 'region':  'NAM'}
    logger.info(fmtkws)

    # merge all indicators of this freq in one dataset
    logger.info(f"Merge {snakemake.wildcards.xrfreq} indicators.")

    with ProgressBar():
        all_ind=[]
        for file in snakemake.input.file:
            ind = xr.open_zarr(file, decode_timedelta=False)
            all_ind.append(ind)
        ds_merge = xr.merge(all_ind,
                                combine_attrs='drop_conflicts')
        ds_merge.attrs['cat:processing_level'] = 'indicators'

        xs.save_to_zarr(ds=ds_merge,
                            filename=str(snakemake.output[0]),
                            rechunk={'time': -1})