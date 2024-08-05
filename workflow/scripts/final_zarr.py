from dask.distributed import Client, LocalCluster
from dask import config as dskconf
from pathlib import Path
import xarray as xr
import shutil
import logging
import tempfile
import os
import xscen as xs
from xscen.io import rechunk
from xscen import (CONFIG, measure_time, timeout)
from utils import move_then_delete

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
        measure_time(name=f'final zarr rechunk', logger=logger),
        timeout(30000, task='final_zarr')
    ):
        # rechunk and move to final destination
        fi_path = Path(f"{CONFIG['paths']['output']}".format(**fmtkws))
        fi_path.parent.mkdir(exist_ok=True, parents=True)
        fi_path_exec = f"{CONFIG['paths']['exec_workdir']}/ESPO-G_workdir/{fi_path.name}"

        specific_temp_dir = CONFIG["io"]["rechunk"]["temp_store"]
        os.makedirs(specific_temp_dir, exist_ok=True)
        temp_dir = tempfile.mkdtemp(dir=specific_temp_dir,
                                    prefix=f"{snakemake.wildcards.sim_id}_{snakemake.wildcards.region}_")

        # rechunk in exec and move to final path after
        rechunk(path_in=str(snakemake.input.clean_up),
                path_out=fi_path_exec,
                chunks_over_dim=CONFIG['custom']['out_chunks'],
                temp_store=temp_dir,
                overwrite=True)

        shutil.move(fi_path_exec, str(snakemake.output[0]))
        shutil.move(snakemake.input.regridded, CONFIG['paths']['regriddir'])


