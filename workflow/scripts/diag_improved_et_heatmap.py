from dask.distributed import Client, LocalCluster
from dask import config as dskconf
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

    cluster = LocalCluster(n_workers=snakemake.resources.n_workers, threads_per_worker=snakemake.params.threads_per_worker,
                           memory_limit=snakemake.params.memory_limit, **daskkws)
    client = Client(cluster)

    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    with (
        measure_time(name=f'diagnostics', logger=logger),
        timeout(2 * 18000, task='diagnostics')
    ):

        meas_datasets = {f"{snakemake.wildcards.sim_id}.{snakemake.wildcards.region}.diag-sim-meas.fx": xr.open_zarr(snakemake.input.sim),
                         f"{snakemake.wildcards.sim_id}.{snakemake.wildcards.region}.diag-scen-meas.fx": xr.open_zarr(snakemake.input.scen)}

        hm = xs.diagnostics.measures_heatmap(meas_datasets)

        ip = xs.diagnostics.measures_improvement(meas_datasets)

        xs.save_to_zarr(hm, str(snakemake.output.diag_heatmap),
                            rechunk=CONFIG['custom']['rechunk'])

        xs.save_to_zarr(ip, str(snakemake.output.diag_improved),
                            rechunk=CONFIG['custom']['rechunk'])
