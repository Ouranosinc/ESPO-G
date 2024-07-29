from dask.distributed import Client, LocalCluster
from dask import config as dskconf
import atexit
import xarray as xr
import logging
import xscen as xs
from xscen import (
    CONFIG,
    measure_time, send_mail)


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads_per_worker,
                           memory_limit=f"{snakemake.params. memory_limit}MB", **daskkws)
    client = Client(cluster)

    fmtkws = {'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    with (
        client,
        measure_time(name=f'health_checks', logger=logger)
    ):
        ds_input = xr.open_zarr(snakemake.input[0], decode_timedelta=False)

        hc = xs.diagnostics.health_checks(
            ds=ds_input,
            **CONFIG['health_checks'])

        hc.attrs.update(ds_input.attrs)
        hc.attrs['cat:processing_level'] = 'health_checks'

        xs.save_to_zarr(hc, str(snakemake.output[0]))


