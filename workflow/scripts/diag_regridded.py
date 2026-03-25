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
    input_b = snakemake.input.bilinear
    input_c = snakemake.input.conservative
    input_prop_ref = snakemake.input.prop_ref
    coords = snakemake.input.coords
    output_prop_bilinear = snakemake.output.prop_bilinear
    output_prop_conservative = snakemake.output.prop_conservative
    output_meas_bilinear = snakemake.output.meas_bilinear
    output_meas_conservative = snakemake.output.meas_conservative
    dregion = snakemake.wildcards.dregion
    config = deepcopy(snakemake.config)
    
    # FIXME: Can't use Dask until the PR in xsdba is merged.
    # # Start Dask cluster
    # client=dask_cluster(
    #     n_workers=snakemake.params.n_workers,
    #     cpus_per_task=snakemake.params.cpus_per_task,
    #     mem=snakemake.params.mem,
    #     local_directory=Path(config['tmppath']) / "dask",
    #     **config['dask'].get('client', {})
    #     )

    ds_b = xr.open_zarr(input_b, decode_timedelta=False)
    ds_c = xr.open_zarr(input_c, decode_timedelta=False)
    if "loc" in ds_b.dims:
        ds_b = xs.utils.unstack_fill_nan(ds_b, coords=str(coords))
    if "loc" in ds_c.dims:
        ds_c = xs.utils.unstack_fill_nan(ds_c, coords=str(coords))

    ds_b = xs.spatial.subset(ds_b, **config['diagregion'][dregion])
    ds_c = xs.spatial.subset(ds_c, **config['diagregion'][dregion])
    ds_ref_prop = xr.open_zarr(input_prop_ref, decode_timedelta=False)

    # Add temperatures to the conservative regridded dataset to be able to compute the diagnostics.
    for v in ["tasmin", "tasmax", "dtr"]:
        if v not in ds_c:
            ds_c[v] = ds_b[v].copy()

    # FIXME: Continuation of the Dask/xsdba issue.
    ds_b = xs.utils.stack_drop_nans(ds_b, mask=ds_b["tasmax"].isel(time=0).notnull().drop_vars("time").load(), to_file=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_regridded_bilinear_{dregion}_{Path(input_b).stem}.nc"))
    ds_b = ds_b.load()
    ds_c = xs.utils.stack_drop_nans(ds_c, mask=ds_c["pr"].isel(time=0).notnull().drop_vars("time").load(), to_file=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_regridded_conservative_{dregion}_{Path(input_c).stem}.nc"))
    ds_c = ds_c.load()
    ds_ref_prop = xs.utils.stack_drop_nans(ds_ref_prop, mask=ds_ref_prop[[v for v in ds_ref_prop.data_vars][0]].notnull().load())
    ds_ref_prop = ds_ref_prop.load()
    ds_ref_prop_b = ds_ref_prop.sel(loc=ds_b["loc"])
    ds_ref_prop_c = ds_ref_prop.sel(loc=ds_c["loc"])

    # Diagnostics
    ds_simb_prop, ds_simb_meas = xs.properties_and_measures(ds=ds_b, dref_for_measure=ds_ref_prop_b, **config['diagnostics']['properties_and_measures'])
    ds_simc_prop, ds_simc_meas = xs.properties_and_measures(ds=ds_c, dref_for_measure=ds_ref_prop_c, **config['diagnostics']['properties_and_measures'])

    # FIXME: Continuation of the Dask/xsdba issue.
    for c in ds_simb_prop.coords:
        if c not in ds_simb_meas.coords:
            ds_simb_meas.coords[c] = ds_simb_prop.coords[c]
    for c in ds_simc_prop.coords:
        if c not in ds_simc_meas.coords:
            ds_simc_meas.coords[c] = ds_simc_prop.coords[c]
    ds_simb_prop = xs.utils.unstack_fill_nan(ds_simb_prop, coords=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_regridded_bilinear_{dregion}_{Path(input_b).stem}.nc"))
    ds_simb_meas = xs.utils.unstack_fill_nan(ds_simb_meas, coords=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_regridded_bilinear_{dregion}_{Path(input_b).stem}.nc"))
    ds_simc_prop = xs.utils.unstack_fill_nan(ds_simc_prop, coords=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_regridded_conservative_{dregion}_{Path(input_c).stem}.nc"))
    ds_simc_meas = xs.utils.unstack_fill_nan(ds_simc_meas, coords=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_regridded_conservative_{dregion}_{Path(input_c).stem}.nc"))

    # Save
    def _save(ds, output):
        if Path(output).suffix == '.zip':
            tmp_zarr_and_zip(ds, output, rechunk=config['chunks']['diag'], encoding={v: {"dtype": "float32"} for v in ds.data_vars})
        else:
            xs.save_to_zarr(ds, output, rechunk=config['chunks']['diag'], encoding={v: {"dtype": "float32"} for v in ds.data_vars})
    _save(ds_simb_prop, output_prop_bilinear)
    _save(ds_simb_meas, output_meas_bilinear)
    _save(ds_simc_prop, output_prop_conservative)
    _save(ds_simc_meas, output_meas_conservative)
