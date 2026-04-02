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
    input_scen = snakemake.input.scen
    # input_prop_ref = snakemake.input.prop_ref
    output_prop = snakemake.output.prop
    # output_meas = snakemake.output.meas
    dregion = snakemake.wildcards.dregion
    config = deepcopy(snakemake.config)
    
    # FIXME: Can't use Dask until the PR in xsdba is merged.
    # Start Dask cluster
    client=dask_cluster(
        n_workers=snakemake.params.n_workers,
        cpus_per_task=snakemake.params.cpus_per_task,
        mem=snakemake.params.mem,
        local_directory=Path(config['tmppath']) / "dask",
        **config['dask'].get('client', {})
        )

    ds_scen = xs.spatial.subset(xr.open_zarr(input_scen, decode_timedelta=False), **config['diagregion'][dregion])
    # ds_ref_prop = xr.open_zarr(input_prop_ref, decode_timedelta=False)

    # FIXME: Continuation of the Dask/xsdba issue.
    ds_scen = xs.utils.stack_drop_nans(ds_scen, mask=ds_scen["tasmax"].isel(time=0).notnull().drop_vars("time").load(), to_file=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_scen_{dregion}_{Path(input_scen).stem}.nc"))
    # ds_scen = ds_scen.load()
    # ds_ref_prop = xs.utils.stack_drop_nans(ds_ref_prop, mask=ds_ref_prop[[v for v in ds_ref_prop.data_vars][0]].notnull().load())
    # ds_ref_prop = ds_ref_prop.load()
    # ds_ref_prop = ds_ref_prop.sel(loc=ds_scen["loc"])

    # Diagnostics
    ds_sim_prop, _ = xs.properties_and_measures(ds=ds_scen.chunk({"time": -1}), **config['diagnostics']['properties_and_measures'])
    # ds_sim_prop, ds_sim_meas = xs.properties_and_measures(ds=ds_scen, dref_for_measure=ds_ref_prop, **config['diagnostics']['properties_and_measures'])

    # # FIXME: Continuation of the Dask/xsdba issue.
    # for c in ds_sim_prop.coords:
    #     if c not in ds_sim_meas.coords:
    #         ds_sim_meas.coords[c] = ds_sim_prop.coords[c]
    ds_sim_prop = xs.utils.unstack_fill_nan(ds_sim_prop, coords=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_scen_{dregion}_{Path(input_scen).stem}.nc"))
    # ds_sim_meas = xs.utils.unstack_fill_nan(ds_sim_meas, coords=str(Path(os.environ['SLURM_TMPDIR']) / f"coords_diag_scen_{dregion}_{Path(input_scen).stem}.nc"))

    # Save
    def _save(ds, output):
        if Path(output).suffix == '.zip':
            tmp_zarr_and_zip(ds, output, rechunk=config['chunks']['diag'], encoding={v: {"dtype": "float32"} for v in ds.data_vars})
        else:
            xs.save_to_zarr(ds, output, rechunk=config['chunks']['diag'], encoding={v: {"dtype": "float32"} for v in ds.data_vars})
    _save(ds_sim_prop, output_prop)
    # _save(ds_sim_meas, output_meas)
