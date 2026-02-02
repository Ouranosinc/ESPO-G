from pathlib import Path
from dask.distributed import Client, LocalCluster
import os
import xscen as xs
if 1==0: #trick vscode
    import snakemake


def dask_cluster(n_workers, cpus_per_task, mem, local_directory, **kwargs):
    cluster = LocalCluster(
        n_workers=n_workers,
        threads_per_worker=cpus_per_task/n_workers,
        memory_limit=f"{int(int(mem.replace('GB',''))/n_workers)}GB",
        local_directory=local_directory,
         **kwargs
    )
    client = Client(cluster)
    print(client.dashboard_link)
    return client


def create_tmp_path(path):
    return f"{os.environ['SLURM_TMPDIR']}/{Path(path).name.replace('.zip','')}"


def tmp_zarr_and_zip(ds, p, delete_tmp=False, **kwargs):
    tmp_path=create_tmp_path(p)
    xs.save_to_zarr(ds, tmp_path, **kwargs)
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    xs.io.zip_directory(tmp_path, p, delete=delete_tmp)
