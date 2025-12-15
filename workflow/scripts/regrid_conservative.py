from copy import deepcopy
from pathlib import Path
import xarray as xr
import xscen as xs
import os
import xclim as xc
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    input_extract = snakemake.input.extract
    input_noleap = snakemake.input.noleap
    coords = snakemake.input.coords
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

    # Open datasets
    ds_input = xr.open_zarr(input_extract, decode_timedelta=False)
    ds_target = xr.open_zarr(input_noleap, decode_timedelta=False)

    # Adjust intermediate grids
    if "intermediate_grids" in config["regrid_conservative"]["regrid_dataset"]:
        intermediate_grids = deepcopy(config["regrid_conservative"]["regrid_dataset"]["intermediate_grids"])
        est_res = xs.spatial._estimate_grid_resolution(ds_input)
        for key, grid_info in intermediate_grids.items():
            if grid_info["cf_grid_2d"]["d_lon"] > est_res[0] or grid_info["cf_grid_2d"]["d_lat"] > est_res[1]:
                # Delete intermediate grids that are too coarse
                intermediate_grids.pop(key)
        if len(intermediate_grids) > 0:
            config["regrid_conservative"]["regrid_dataset"]["intermediate_grids"] = intermediate_grids
        else:
            config["regrid_conservative"]["regrid_dataset"].pop("intermediate_grids")

    # Conservative regridding cannot be done with locstream_out=True
    ds_target_2d = xs.utils.unstack_fill_nan(ds_target, coords=str(coords))
    ds_target_2d["mask"] = xr.where(ds_target_2d["mask"] >= 1, 1, 0)

    # Only precipitation is regridded conservatively
    ds_input = ds_input[["pr", "mask"]]
    
    ds_regrid = xs.regrid_dataset(
        ds=ds_input,
        ds_grid=ds_target_2d,
        weights_location=Path(os.environ['SLURM_TMPDIR']) / "weights",
        **config["regrid_conservative"]["regrid_dataset"]
    )

    # Put back to stacked form
    ds_regrid = xs.utils.stack_drop_nans(ds_regrid, mask=ds_target_2d["mask"].astype(bool).load())

    # Chunk the time dimension
    chunks = xs.utils.translate_time_chunk({'time': '4year'},
                                            xc.core.calendar.get_calendar(ds_regrid),
                                            ds_regrid.time.size)
    
    # Save
    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(ds_regrid, output, rechunk=chunks, encoding={v: {"dtype": "float32"} for v in ds_regrid.data_vars})
    else:
        xs.save_to_zarr(ds_regrid, output, rechunk=chunks, encoding={v: {"dtype": "float32"} for v in ds_regrid.data_vars})
