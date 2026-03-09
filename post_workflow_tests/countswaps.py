
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

xs.load_config( "paths_post-workflow.yml")
ids=[
    'CMIP6_CORDEX_MPI-ESM1-2-LR_r1i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12',
    #'CMIP6_CORDEX_CanESM5_r1i1p2f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12',
    #'CMIP6_CORDEX_NorESM2-MM_r1i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12',
                         ]

if __name__ == '__main__':

    for sim_id in ids:
        print(sim_id)
        for i in range(6):
            ds_tasmax= xr.open_zarr(f"{CONFIG['regTasmin']}/{sim_id}+NAM+CaSR+sr-{i}+tasmax+adjusted.zarr")
            ds_tasmin= xr.open_zarr(f"{CONFIG['regTasmin']}/{sim_id}+NAM+CaSR+sr-{i}+tasmin+adjusted.zarr")
            inversion= ds_tasmin.tasmin>ds_tasmax.tasmax
            
            df = inversion.to_dataframe(name='inversion').reset_index()
            df = df[df.inversion]

            df.to_csv(f"{CONFIG['pathind']}/inversions/{sim_id}_sr-{i}_inversions.csv", index=False)



