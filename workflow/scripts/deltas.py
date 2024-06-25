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

    fmtkws = {'xrfreq': snakemake.wildcards.xrfreq, 'sim_id': snakemake.wildcards.sim_id, 'region':  'NAM'}
    logger.info(fmtkws)

    for delta_task, kind in zip(["abs-delta","per-delta"], ['+','%']):
        ref_horizon=CONFIG['aggregate']['compute_deltas']['reference_horizon']
        with (
             Client(n_workers=4, threads_per_worker=4,memory_limit="6GB", **daskkws),
             xs.measure_time(name=f'{delta_task} {ref_horizon} {snakemake.wildcards.sim_id}',logger=logger),
        ):

             if delta_task=="abs-delta":
                ind_dict = xr.open_zarr(snakemake.input[0], decode_timedelta=False)
                ds_delta = xs.aggregate.compute_deltas(ds=ind_dict,
                                                       kind=kind,
                                                       to_level=f"{delta_task}-{ref_horizon}")
                xs.save_to_zarr(ds_delta, str(snakemake.output.abs_delta), rechunk={'time': 4} | CONFIG['custom']['rechunk'])
             elif delta_task == "per-delta":
                 variable = ['aggregate']['input']['per-delta']['variable']
                 ind_dict = xr.open_zarr(snakemake.input[0], group=variable, decode_timedelta=False)
                 ds_delta = xs.aggregate.compute_deltas(ds=ind_dict,
                                                        kind=kind,
                                                        to_level=f"{delta_task}-{ref_horizon}")
                 xs.save_to_zarr(ds_delta, str(snakemake.output.per_delta),
                                 rechunk={'time': 4} | CONFIG['custom']['rechunk'])

        # move to final destination
        # large_move(exec_wdir,"delta", CONFIG['paths']['delta'], pcat)