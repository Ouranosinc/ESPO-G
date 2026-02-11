from dask.distributed import Client
import os
from xsdba.base import Grouper, map_blocks, map_groups
from xsdba.nbutils import quantile
import numpy as np
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

xs.load_config("../config/config_ESPO-R-DQM.yml", "../config/paths_ESPO-R-DQM.yml")


if __name__ == '__main__':

    with Client(
            n_workers=4, memory_limit="100GB",
            dashboard_address= 6788,
            local_directory=os.environ['SLURM_TMPDIR'],
        ):
        count=[]

        for i in range(6):
            ds_tasmax= xr.open_zarr(f"{CONFIG['regTasmin']}/CMIP6_CORDEX_MPI-ESM1-2-LR_r1i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12+NAM+CaSR+sr-{i}+tasmax+adjusted.zarr")
            ds_tasmin= xr.open_zarr(f"{CONFIG['regTasmin']}/CMIP6_CORDEX_MPI-ESM1-2-LR_r1i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12+NAM+CaSR+sr-{i}+tasmin+adjusted.zarr")
            inversion= ds_tasmin.tasmin>ds_tasmax.tasmax

            df = inversion.to_dataframe(name='inversion').reset_index()
            df = df[df.inversion]
            df.to_csv(f"{CONFIG['regTasmin']}/inversion_sr{i}.csv", index=False)
            c=len(df)
            print(c)
            count.append(c)
        print('total')
        print(np.sum(count))