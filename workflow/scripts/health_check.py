from copy import deepcopy
from pathlib import Path
import xarray as xr
import xscen as xs
try:
    from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
except ImportError:
    from inpact.scripts.utils import save_to_zarrzip as tmp_zarr_and_zip
    from inpact.scripts.utils import dask_cluster
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

    diags = deepcopy(config['health_checks'])
    if "missing" in diags:
        diags_missing = diags.pop("missing")
        ds_for_missing = xs.utils.stack_drop_nans(
            ds_input,
            mask=ds_input[[v for v in ds_input.data_vars if "mask" not in v][0]].isel(time=0).notnull().drop_vars('time').load()
            )
        xs.diagnostics.health_checks(
            ds=ds_for_missing,
            missing=diags_missing,
            raise_on=["missing"]
        )

    hc = xs.diagnostics.health_checks(
        ds=ds_input,
        **diags
        )
    
    hc.attrs.update(ds_input.attrs)

    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(hc, output)
    else:
        xs.save_to_zarr(hc, output)

