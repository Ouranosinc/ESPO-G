from copy import deepcopy
from pathlib import Path
import xarray as xr
import xscen as xs
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    input = snakemake.input
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
    
    ds_input = xr.open_mfdataset(input, engine='zarr', decode_timedelta=False)

    hc = xs.diagnostics.health_checks(
        ds=ds_input,
        **config['health_checks']
        )
    
    hc.attrs.update(ds_input.attrs)

    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(hc, output)
    else:
        xs.save_to_zarr(hc, output)

