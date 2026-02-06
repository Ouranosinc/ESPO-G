from copy import deepcopy
import xscen as xs
import xclim as xc
import xarray as xr
import numpy as np
from datetime import datetime
xr.set_options(keep_attrs=True)
from workflow.scripts.utils import dask_cluster
from xscen.xclim_modules import conversions
from pathlib import Path
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    inputs=snakemake.input
    output=snakemake.output
    config = deepcopy(snakemake.config)

    ds_tasmax= xr.open_zarr(inputs['tasmax'], decode_timedelta=False)
    ds_tasmin= xr.open_zarr(inputs['tasmin'], decode_timedelta=False)

    # Find where no inversion
    valid_mask = ds_tasmax.tasmax > ds_tasmin.tasmin


    ds_tasmax['tasmax']=ds_tasmax.tasmax.where(valid_mask.compute(),
     other=ds_tasmin.tasmin)

    ds_tasmin['tasmin']=ds_tasmin.tasmin.where(valid_mask.compute(),
        other=ds_tasmax.tasmax)
    
    
    xs.save_to_zarr(
        ds_tasmin, 
        output.tasmin, 
        **config['save_to_zarr'],
        )

    xs.save_to_zarr(
        ds_tasmax, 
        output.tasmax, 
        **config['save_to_zarr'],
        )


    ds_pr= xr.open_zarr(inputs['pr'], decode_timedelta=False)
    ds_dtr= xr.open_zarr(inputs['dtr'], decode_timedelta=False)

    xs.save_to_zarr(
        ds_pr, 
        output.pr, 
        **config['save_to_zarr'],
        )

    xs.save_to_zarr(
        ds_dtr, 
        output.dtr, 
        **config['save_to_zarr'],
        )


