from copy import deepcopy
from pathlib import Path
from dask.distributed import Client, LocalCluster
import os
import xscen as xs
#from xscen import CONFIG
from zipfile import ZipFile
import shutil as sh
import tempfile
if 1==0: #trick vscode
    import snakemake

#xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

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



def create_tmp_path(path):
    if 'SLURM_TMPDIR' in os.environ:
        return f"{os.environ['SLURM_TMPDIR']}/{Path(path).name.replace('.zip','')}"
    else:
        #TODO: figure out how to put this in config, but not load config here..
        with tempfile.TemporaryDirectory(dir='/exec/jlavoie/tmpdir') as tmpdirname:
            return f"{tmpdirname}/{Path(path).name.replace('.zip','')}"

def tmp_zarr_and_zip(ds, p, delete_tmp=False, **kwargs):
    tmp_path=create_tmp_path(p)
    xs.save_to_zarr(ds, tmp_path, **kwargs)
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    xs.io.zip_directory(tmp_path, p, delete=delete_tmp)


def save(ds, p, delete_tmp=False, **kwargs):
    if Path(p).suffix == '.zip':
        tmp_zarr_and_zip(ds, p, delete_tmp=False, **kwargs)
    else:
        xs.save_to_zarr(ds, p, **kwargs)