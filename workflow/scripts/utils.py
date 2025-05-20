from pathlib import Path
from dask.distributed import Client, LocalCluster
import os
import xscen as xs
from xscen import CONFIG
from zipfile import ZipFile
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config-general.yml", "config/config-region.yml", "config/paths.yml")


def dask_cluster(params):
    cluster = LocalCluster(
        n_workers=params.n_workers,
        threads_per_worker=params.cpus_per_task/params.n_workers,
        memory_limit=f"{int(int(params.mem.replace('GB',''))/params.n_workers)}GB",
        local_directory=os.environ['SLURM_TMPDIR'], **CONFIG['dask'].get('client', {}))
    client = Client(cluster)
    return client

# eventually take this from xscen
def zip_directory(root, zipfile, **zip_args):
    root = Path(root)

    def _add_to_zip(zf, path, root):
        zf.write(path, path.relative_to(root))
        if path.is_dir():
            for subpath in path.iterdir():
                _add_to_zip(zf, subpath, root)

    with ZipFile(zipfile, "w", **zip_args) as zf:
        for file in root.iterdir():
            _add_to_zip(zf, file, root)


def create_tmp_path(path):
    return f"{os.environ['SLURM_TMPDIR']}/{Path(path).name.replace('.zip','')}"

def tmp_zarr_and_zip(ds, p):
    tmp_path=create_tmp_path(p)
    xs.save_to_zarr(ds, tmp_path)
    xs.io.zip_directory(tmp_path, p)