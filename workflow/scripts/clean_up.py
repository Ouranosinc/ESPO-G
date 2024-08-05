from dask.distributed import Client, LocalCluster
from dask import config as dskconf
import logging
import xscen as xs
import xarray as xr
from xscen import (search_data_catalogs,
    extract_dataset,
    CONFIG,measure_time, timeout, clean_up)

xr.set_options(keep_attrs=True)

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads_per_worker,
                           memory_limit=snakemake.params.memory_limit, **daskkws)
    client = Client(cluster)

    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    with (
          measure_time(name=f'cleanup', logger=logger),
          timeout(18000, task='clean_up')
    ):
        # get all adjusted data
        ds = xr.open_mfdataset(snakemake.input, engine='zarr')
        ds = ds.assign(tasmin=(ds.tasmax - ds.dtr))
        ds = ds.drop_vars('dtr')
        ds = clean_up(ds=ds,
                      **CONFIG['clean_up']['xscen_clean_up']
                      )

        # fix the problematic data
        logger.info('Mask grid cells where tasmin < 100 K.')
        ds = ds.where(ds.tasmin > 100)

        xs.save_to_zarr(ds, str(snakemake.output[0]), itervar=True)
