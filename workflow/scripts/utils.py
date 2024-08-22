from pathlib import Path
from dask.distributed import Client, LocalCluster
import os
import xscen as xs
from xscen import CONFIG

xs.load_config("config/config.yml","config/paths.yml")
1

def dask_cluster(params):
    cluster = LocalCluster(
        n_workers=params.n_workers,
        threads_per_worker=params.cpus_per_task/params.n_workers,
        memory_limit=f"{int(int(params.mem.replace('GB',''))/params.n_workers)}GB",
        local_directory=os.environ['SLURM_TMPDIR'], **CONFIG['dask'].get('client', {}))
    client = Client(cluster)
    return client
