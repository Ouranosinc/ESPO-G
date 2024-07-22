from dask.distributed import Client
from dask import config as dskconf
import atexit
import xarray as xr
import logging
import xscen as xs
from xscen import (
    CONFIG,
    measure_time, timeout)


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])


    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    with (
        Client(n_workers=3, threads_per_worker=5,
               memory_limit="20GB", **daskkws),
        measure_time(name=f'diagnostics', logger=logger),
        timeout(2 * 18000, task='diagnostics')
    ):


        # make sur sim is first (for improved)
        # order_keys = [f'{snakemake.wildcards.sim_id}.{snakemake.wildcards.region}.diag-sim-meas.fx',
        #               f'{snakemake.wildcards.sim_id}.{snakemake.wildcards.region}.diag-scen-meas.fx']
        # meas_datasets = {k: meas_datasets[k] for k in order_keys}

        meas_datasets = {f"{snakemake.wildcards.sim_id}.{snakemake.wildcards.region}.diag-sim-meas.fx": xr.open_zarr(snakemake.input.sim),
                         f"{snakemake.wildcards.sim_id}.{snakemake.wildcards.region}.diag-scen-meas.fx": xr.open_zarr(snakemake.input.scen)}

        hm = xs.diagnostics.measures_heatmap(meas_datasets)

        ip = xs.diagnostics.measures_improvement(meas_datasets)

        xs.save_to_zarr(hm, str(snakemake.output.diag_heatmap),
                            rechunk=CONFIG['custom']['rechunk'])

        xs.save_to_zarr(ip, str(snakemake.output.diag_improved),
                            rechunk=CONFIG['custom']['rechunk'])

        xs.send_mail(
                subject=f"{snakemake.wildcards.sim_id}/{snakemake.wildcards.region} - Succès",
                msg=f"Toutes les étapes demandées pour la simulation {snakemake.wildcards.sim_id}/{snakemake.wildcards.region} ont été accomplies.")