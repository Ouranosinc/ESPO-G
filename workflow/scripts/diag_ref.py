from copy import deepcopy
from pathlib import Path
import os
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
    input = snakemake.input.ref
    output = snakemake.output.prop
    dregion = snakemake.wildcards.dregion
    config = deepcopy(snakemake.config)
    
    # Start Dask cluster
    client=dask_cluster(
        n_workers=snakemake.params.n_workers,
        cpus_per_task=snakemake.params.cpus_per_task,
        mem=snakemake.params.mem,
        local_directory=Path(config['tmppath']) / "dask",
        **config['dask'].get('client', {})
        )

    ds_ref = xs.spatial.subset(xr.open_zarr(input, decode_timedelta=False), **config['diagregion'][dregion])

    # Much easier on Dask if we drop the NaN values at this stage, and then re-stack them after the diagnostics.
    ds_ref = xs.utils.stack_drop_nans(ds_ref, mask=ds_ref["tasmax"].isel(time=0).notnull().drop_vars("time").load(), to_file=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_ref_{dregion}_{Path(input).stem}.nc"))

    # Add tas
    ds_ref["tas"] = (ds_ref["tasmax"] + ds_ref["tasmin"]) / 2
    ds_ref["tas"].attrs = ds_ref["tasmax"].attrs

    # Diagnostics
    ds_ref_prop, _ = xs.properties_and_measures(ds=ds_ref, **config['diagnostics']['properties_and_measures'])
    ds_ref_prop = xs.utils.unstack_fill_nan(ds_ref_prop, coords=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_ref_{dregion}_{Path(input).stem}.nc"))

    # Save
    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(ds_ref_prop, output, rechunk=config['chunks']['diag'], encoding={v: {"dtype": "float32"} for v in ds_ref_prop.data_vars})
    else:
        xs.save_to_zarr(ds_ref_prop, output, rechunk=config['chunks']['diag'], encoding={v: {"dtype": "float32"} for v in ds_ref_prop.data_vars})
