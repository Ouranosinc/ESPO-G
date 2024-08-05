from dask.distributed import Client, LocalCluster
from dask import config as dskconf
import xarray as xr
import logging
import xscen as xs
from xscen import (CONFIG,
    measure_time)

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads_per_worker,
                           memory_limit=snakemake.params.memory_limit, **daskkws)
    client = Client(cluster)

    fmtkws = {'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

# iter over all sim meas
    meas_dict = xr.open_zarr(snakemake.input.sim)

    with (
        measure_time(name=f'off-diag-meas {snakemake.wildcards.dom_name} {snakemake.wildcards.sim_id}',
                     logger=logger),
    ):
        # get scen meas
        meas_datasets = {}
        meas_datasets[f'{snakemake.wildcards.sim_id}.{snakemake.wildcards.dom_name}.diag-sim-meas'] = meas_dict
        meas_datasets[f'{snakemake.wildcards.sim_id}.{snakemake.wildcards.dom_name}.diag-scen-meas'] = xr.open_zarr(snakemake.input.scen)

        ip = xs.diagnostics.measures_improvement(meas_datasets)

        # save and update
        xs.save_to_zarr(ip, str(snakemake.output[0]))

    # move to final destination
# large_move(exec_wdir, "", CONFIG['paths']['final_diag'], pcat)