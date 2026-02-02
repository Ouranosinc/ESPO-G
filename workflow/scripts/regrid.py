from copy import deepcopy
from pathlib import Path
import numpy as np
import xarray as xr
import xscen as xs
import os
import xclim as xc
import random
try:
    from workflow.scripts.utils import tmp_zarr_and_zip
except ImportError:
    from inpact.scripts.utils import save_to_zarrzip as tmp_zarr_and_zip

if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    input_extract = snakemake.input.extract
    input_noleap = snakemake.input.noleap
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)

    # Open datasets
    ds_input = xr.open_zarr(input_extract, decode_timedelta=False)
    ds_target = xr.open_zarr(input_noleap, decode_timedelta=False)

    # Adjust intermediate grids
    if "intermediate_grids" in config["regrid"]["regrid_dataset"]:
        intermediate_grids = deepcopy(config["regrid"]["regrid_dataset"]["intermediate_grids"])
        grids = deepcopy(intermediate_grids)
        est_res = xs.spatial._estimate_grid_resolution(ds_input)
        for key, grid_info in grids.items():
            if grid_info["cf_grid_2d"]["d_lon"] > est_res[0] or grid_info["cf_grid_2d"]["d_lat"] > est_res[1]:
                # Delete intermediate grids that are too coarse
                intermediate_grids.pop(key)
        if len(intermediate_grids) > 0:
            config["regrid"]["regrid_dataset"]["intermediate_grids"] = intermediate_grids
        else:
            config["regrid"]["regrid_dataset"].pop("intermediate_grids")

    ds_regrid = xs.regrid_dataset(
        ds=ds_input,
        ds_grid=ds_target,
        weights_location=Path(os.environ['SLURM_TMPDIR']) / "weights" / f"regrid_weights_{random.randint(0,1e10)}",
        **config["regrid"]["regrid_dataset"]
    )

    # Chunk the time dimension
    chunks = xs.utils.translate_time_chunk({'time': '4year'},
                                            xc.core.calendar.get_calendar(ds_regrid),
                                            ds_regrid.time.size)
    
    # Save
    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(ds_regrid, output, rechunk=chunks, encoding={v: {"dtype": "float32"} for v in ds_regrid.data_vars})
    else:
        xs.save_to_zarr(ds_regrid, output, rechunk=chunks, encoding={v: {"dtype": "float32"} for v in ds_regrid.data_vars})
