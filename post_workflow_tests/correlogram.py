
import xscen as xs
import xarray as xr
from xscen import CONFIG
import xclim as xc
import datetime
from dask.distributed import Client
import os
import sys
import time
import glob
from pathlib import Path
import xsdba

xs.load_config( "paths_post-workflow.yml")


if __name__ == '__main__':
    # print('reference')
    # ds = xr.open_zarr(f"{CONFIG['DQM']}/reference/NAM_CaSR_default.zarr.zip")
    # ds=xs.spatial.subset(ds, method='bbox',lon_bnds= [-83 ,-55 ] ,lat_bnds= [42, 53], name='atlas')
    # ds= ds.sel(time=slice('1991','2020'))
    # for var in ['pr','tasmin','tasmax']:
    #     path=f"{CONFIG['pathind']}/CaSR_atlas_correlogram-{var}.zarr.zip"
    #     if not Path(path).exists():
    #         out=xsdba.properties.spatial_correlogram(ds[var].compute(), dims=['rlat','rlon'], bins=300)
    #         xs.save_to_zarr(
    #             out.to_dataset(),
    #             path,
    #             zip_zarrdir= "${SLURM_TMPDIR}",
    #             )
    
    # print('adjusted')
    # for m in ['tasmin','DQM','Scaling']:
    #     for dm in ['MPI-ESM1-2-LR','CanESM5','NorESM2-MM']:
    #         print(glob.glob(f"{CONFIG[m]}/staging/simulation/biasadjusted/*_v20_CaSR/CMIP6/CORDEX/NAM/OURANOS/CRCM5-SN/{dm}/*/ssp370/r1/day/*/*.zarr.zip"))
    #         ds= xr.open_mfdataset(
    #             glob.glob(f"{CONFIG[m]}/staging/simulation/biasadjusted/*_v20_CaSR/CMIP6/CORDEX/NAM/OURANOS/CRCM5-SN/{dm}/*/ssp370/r1/day/*/*.zarr.zip"),
    #             engine='zarr')
    #         ds=xs.spatial.subset(ds, method='bbox',lon_bnds= [-83 ,-55 ] ,lat_bnds= [42, 53], name='atlas')
    #         ds= ds.sel(time=slice('1991','2020'))

    #         for var in ['pr','tasmin','tasmax']:

    #             path=f"{CONFIG['pathind']}/{m}_{dm}_atlas_correlogram-{var}.zarr.zip"
    #             if not Path(path).exists():
    #                 out=xsdba.properties.spatial_correlogram(ds[var].compute(), dims=['rlat','rlon'], bins=300)
    #                 xs.save_to_zarr(
    #                     out.to_dataset(),
    #                     path,
    #                     zip_zarrdir= "${SLURM_TMPDIR}",
    #                     )
    
    print('extracted')
    cat=xs.DataCatalog(CONFIG['catsim'])
    sftlf= cat.search(source='CRCM5-SN', variable='sftlf',id='CMIP6_CORDEX_MPI-ESM1-2-LR_r1i1p1f1_OURANOS_CRCM5-SN_historical_r1_NAM-12' ).to_dataset()

    #for dm in ['MPI-ESM1-2-LR','CanESM5','NorESM2-MM']:
    for dm in ['MPI-ESM1-2-LR']:
        print(dm)
        f= glob.glob(f"{CONFIG['regDQM']}/*_{dm}_*+extracted.zarr")[0]
        ds=xr.open_zarr(f, decode_timedelta=False)
        ds=ds.where(sftlf.sftlf>=0.25)
        ds=xs.spatial.subset(ds, method='bbox',lon_bnds= [-83 ,-55 ] ,lat_bnds= [42, 53], name='atlas')
        ds= ds.sel(time=slice('1991','2020'))

        for var in ['pr','tasmin','tasmax']:

            path=f"{CONFIG['pathind']}/extracted_{dm}_atlas_correlogram-{var}.zarr.zip"
            if not Path(path).exists():
                out=xsdba.properties.spatial_correlogram(ds[var].compute(), dims=['rlat','rlon'], bins=300)
                xs.save_to_zarr(
                    out.to_dataset(),
                    path,
                    zip_zarrdir= "${SLURM_TMPDIR}",
                    )