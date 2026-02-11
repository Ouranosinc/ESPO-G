from dask.distributed import Client
import os
from xsdba.base import Grouper, map_blocks, map_groups
from xsdba.nbutils import quantile
import pandas as pd
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
import numpy as np

xs.load_config("../config/config_ESPO-R-DQM.yml", "../config/paths_ESPO-R-DQM.yml")
cat=xs.DataCatalog(CONFIG['extraction']['simulation']['search_data_catalogs']['data_catalogs'][0])

catr=xs.DataCatalog(CONFIG['extraction']['reference']['CaSR']['search_data_catalogs']['data_catalogs'][0])


if __name__ == '__main__':
    count=[]
    q99= xr.open_zarr(f"{CONFIG['regDQM']}/q99/q99_climref.zarr.zip")
    q99=xs.utils.stack_drop_nans(q99, q99.pr.isel(dayofyear=0, quantiles=0, drop=True).notnull().compute())
    d=[]
    for i in range(6):
        d.append(xr.open_zarr(f"{CONFIG['regDQM']}/CMIP6_CORDEX_MPI-ESM1-2-LR_r1i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12+NAM+CaSR+sr-{i}+regridded.zarr"))
    ds=xr.concat(d, dim='loc')
        
    ds=ds.convert_calendar('noleap')
    q99=q99.rename({'dayofyear':'time'})

    ds=ds.chunk({'time':365, 'loc':50})
    q99=q99.chunk({'time':365, 'loc':50})


    d=[]
    for y in range(1950,2101):
        print(y)
        ds_cur= ds.sel(time=str(y))
        q99_cur=q99.copy()
        q99_cur['time']=ds_cur['time']
        q99_cur=q99_cur.squeeze().drop_vars('quantiles')
        out= ds_cur.where((ds_cur.pr > 1000 *q99_cur).compute(), drop=True)
        # ds=ds.where(ds.pr>(1.1574e-05*10))
        
        df = out['pr'].to_dataframe().reset_index()
        
        # # Keep only rows with actual values (removes NaNs)
        df = df.dropna(subset=['pr'])
        count.append(len(df))
        d.append(df)
        df.to_csv(f"{CONFIG['regDQM']}/q99/1000q99ref-{y}.csv")
    print(np.sum(count))

    dftot=pd.concat(d)
    dftot.to_csv(f"{CONFIG['regDQM']}/q99/1000q99ref.csv")