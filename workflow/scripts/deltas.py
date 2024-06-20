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

    fmtkws = {'xrfreq': snakemake.wildcards.xrfreq, 'sim_id': snakemake.wildcards.sim_id, 'region':  snakemake.wildcards.region}
    logger.info(fmtkws)

    for delta_task, kind in zip(["abs-delta","per-delta"], ['+','%']):
        ref_horizon=CONFIG['aggregate']['compute_deltas']['reference_horizon']
        ind_dict = xr.open_zarr(snakemake.input[0])
        for id_input, ds_input in ind_dict.items():

            with (
                 Client(n_workers=4, threads_per_worker=4,memory_limit="6GB", **daskkws),
                 xs.measure_time(name=f'{snakemake.wildcards.delta_task} {ref_horizon} {snakemake.wildcards.sim_id}',logger=logger),
            ):
                 ds_delta = xs.aggregate.compute_deltas(ds=ds_input,
                                                       kind=kind,
                                                       to_level=f"{delta_task}-{ref_horizon}")

                 xs.save_to_zarr(ds_delta, str(snakemake.output[0]), rechunk={'time': 4} | CONFIG['custom']['rechunk'])

        # move to final destination
        # large_move(exec_wdir,"delta", CONFIG['paths']['delta'], pcat)