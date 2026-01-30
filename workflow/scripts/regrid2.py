import xarray as xr
import xscen as xs
import os
import xclim as xc
from copy import deepcopy
if 1==0: #trick vscode
    import snakemake
import sys

if __name__ == '__main__':
    
    # Get Snakemake parameters
    #config = deepcopy(snakemake.config)
    noleap=sys.argv[1]
    extract=sys.argv[2]
    output=sys.argv[3]
    #config = eval(sys.argv[4]) #TODO: figure out better way to pass config

    print(noleap)
    print(extract)
    print(output)
    #print(config)
    #client=dask_cluster(snakemake.params,config['dask']['client'])

    ds_input = xr.open_zarr(extract, decode_timedelta=False)#.compute()

    ds_target = xr.open_zarr(noleap, decode_timedelta=False)#.compute()

    #mask_nan=ds_input.isnull()
    #xs.save_to_zarr(mask_nan, f"/scratch/julavoie/espo-workdir/mask_{snakemake.wildcards.subregion}.zarr")
    #ds_input=ds_input.fillna(99999)

    ds_regrid = xs.regrid_dataset(
        ds=ds_input,
        ds_grid=ds_target,
        #**config['regrid']['regrid_dataset']
        **{'regridder_kwargs': {'method': 'bilinear', 'extrap_method': 'inverse_dist', 'locstream_out': True, 'reuse_weights': False}}
        

    )
    

    # save
    xs.save_to_zarr(ds_regrid, output)#, **config['save_to_zarr'])