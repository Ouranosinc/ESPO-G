from copy import deepcopy
from pathlib import Path
from dask.distributed import Client, LocalCluster
import os
import xscen as xs
#from xscen import CONFIG
from zipfile import ZipFile
import shutil as sh
if 1==0: #trick vscode
    import snakemake

def dask_cluster(params, dask_config=None):
    dask_config = dask_config or {}
    cluster = LocalCluster(
        n_workers=params.n_workers,
        threads_per_worker=params.cpus_per_task/params.n_workers,
        memory_limit=f"{int(int(params.mem.replace('GB',''))/params.n_workers)}GB",
         **dask_config)
    client = Client(cluster)
    print(client.dashboard_link)
    return client

