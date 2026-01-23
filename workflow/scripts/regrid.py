import xarray as xr
import xscen as xs
import os
import xclim as xc
from copy import deepcopy
from workflow.scripts.utils import dask_cluster, save
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    
    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs=snakemake.input
    output=snakemake.output[0]

    #client=dask_cluster(snakemake.params,config['dask']['client'])

    ds_input = xr.open_zarr(inputs['extract'], decode_timedelta=False)#.compute()

    ds_target = xr.open_zarr(inputs['noleap'], decode_timedelta=False)#.compute()

    #mask_nan=ds_input.isnull()
    #xs.save_to_zarr(mask_nan, f"/scratch/julavoie/espo-workdir/mask_{snakemake.wildcards.subregion}.zarr")
    #ds_input=ds_input.fillna(99999)

    ds_regrid = xs.regrid_dataset(
        ds=ds_input,
        ds_grid=ds_target,
        **config['regrid']['regrid_dataset']
    )
    
    #ds_regrid=ds_regrid.where(~mask_nan)

    # chunk time dim
    # ds_regrid = ds_regrid.chunk(
    #     xs.utils.translate_time_chunk({'time': '4year'},
    #                          xc.core.calendar.get_calendar(ds_regrid),
    #                          ds_regrid.time.size)
    #                            )



    # save
    xs.save_to_zarr(ds_regrid, output, **config['save_to_zarr'])