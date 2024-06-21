from dask.distributed import Client
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
    atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])


    fmtkws = {'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    with (
        Client(n_workers=8, threads_per_worker=5,
               memory_limit="5GB", **daskkws),
        measure_time(name=f'health_checks', logger=logger)
    ):
        ds_input = xr.open_zarr(snakemake.input[0], decode_timedelta=False)

        hc = xs.diagnostics.health_checks(
            ds=ds_input,
            **CONFIG['health_checks'])

        hc.attrs.update(ds_input.attrs)
        hc.attrs['cat:processing_level'] = 'health_checks'

        xs.save_to_zarr(hc, str(snakemake.output[0]))

        send_mail(
            subject=f"{snakemake.wildcards.sim_id} - Succès",
            msg=f"{snakemake.wildcards.sim_id} est terminé. \n Health checks:" + "".join(
                [f"\n{var}: {hc[var].values}" for var in hc.data_vars]),
        )

