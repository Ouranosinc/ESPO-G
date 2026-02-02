from copy import deepcopy
from pathlib import Path
import xscen as xs
import xarray as xr
try:
    from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
except ImportError:
    from inpact.scripts.utils import save_to_zarrzip as tmp_zarr_and_zip
    from inpact.scripts.utils import dask_cluster
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    input = snakemake.input[0]
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)
    
    # Start Dask cluster
    client=dask_cluster(
        n_workers=snakemake.params.n_workers,
        cpus_per_task=snakemake.params.cpus_per_task,
        mem=snakemake.params.mem,
        local_directory=Path(config['tmppath']) / "dask",
        **config['dask'].get('client', {})
        )

    ds = xr.open_zarr(input, decode_timedelta=False)

    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(ds, output, rechunk=config['chunks']['working'])
    else:
        xs.save_to_zarr(ds, output, rechunk=config['chunks']['working'])
