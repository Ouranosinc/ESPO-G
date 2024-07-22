from dask.distributed import Client
from dask import config as dskconf
import xarray as xr
import logging
import xscen as xs
from xscen import CONFIG


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')


if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    fmtkws = {'xrfreq': snakemake.wildcards.xrfreq, 'sim_id': snakemake.wildcards.sim_id, 'region': "NAM"}
    logger.info(fmtkws)

    ind_dict = xr.open_zarr(snakemake.input[0], decode_timedelta=False)

    with (
            Client(n_workers=5, threads_per_worker=4,memory_limit="6GB", **daskkws),
            xs.measure_time(name=f'clim {snakemake.wildcards.sim_id}',logger=logger),
    ):
        ds_mean = xs.climatological_mean(ds=ind_dict)

        xs.save_to_zarr(ds_mean, str(snakemake.output[0]),
                        itervar=True,
                        rechunk={'time': 4} | CONFIG['custom']['rechunk'])

# move to final destination
# large_move(exec_wdir,"climatology", CONFIG['paths']['climatology'], pcat)

