from dask.distributed import Client, LocalCluster
from dask import config as dskconf
import xarray as xr
import logging
import xscen as xs
from xclim.sdba import properties
import xclim as xc
from xscen import (CONFIG,adjust, measure_time, timeout)

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads,
               memory_limit="12GB", **daskkws)
    client = Client(cluster)

    with (
            client,
            measure_time(name=f'adjust {snakemake.wildcards.var}', logger=logger),
            timeout(18000, task='adjust')
    ):
        # load sim ds
        ds_sim = xr.open_zarr(snakemake.input.rechunk)
        ds_tr = xr.open_zarr(snakemake.input.train)

        # there are some negative dtr in the data (GFDL-ESM4). This puts is back to a very small positive.
        ds_sim['dtr'] = xc.sdba.processing.jitter_under_thresh(ds_sim.dtr, "1e-4 K")

        # adjust
        ds_scen = adjust(dsim=ds_sim,
                         dtrain=ds_tr,
                         **CONFIG['biasadjust']['variables'][snakemake.wildcards.var]['adjusting_args'])

        xs.save_to_zarr(ds_scen, str(snakemake.output[0]))
