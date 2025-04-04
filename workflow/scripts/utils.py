from pathlib import Path
from dask.distributed import Client, LocalCluster
import os
import xscen as xs
from xscen import CONFIG

xs.load_config("config/config.yml","config/paths.yml")

def dask_cluster(params):
    """ Set up a dask cluster from snakemake params"""
    cluster = LocalCluster(
        n_workers=params.n_workers,
        threads_per_worker=1, #params.cpus_per_task/params.n_workers,
        memory_limit=f"{int(int(params.mem.replace('GB',''))/params.n_workers)}GB", #"200G"
        local_directory=os.environ['SLURM_TMPDIR'], **CONFIG['dask'].get('client', {}))
    client = Client(cluster)
    return client


def create_tmp_path(path):
    return f"{os.environ['SLURM_TMPDIR']}/{Path(path).name.replace('.zip','')}"

def tmp_zarr_and_zip(ds, p):
    tmp_path=create_tmp_path(p)
    xs.save_to_zarr(ds, tmp_path)
    xs.io.zip_directory(tmp_path, p)