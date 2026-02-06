from dask.distributed import Client
import os
from xsdba.base import Grouper, map_blocks, map_groups
from xsdba.nbutils import quantile

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
cat=xs.DataCatalog(CONFIG['extraction']['simulation']['search_data_catalogs']['data_catalogs'][0])



if __name__ == '__main__':

    with Client(
            n_workers=4, memory_limit="200GB",
            local_directory=os.environ['SLURM_TMPDIR'],
        ):

        ds_rawh= cat.search(source='CRCM5-SN',driving_model='MPI-ESM1-2-LR', experiment='historical', variable='pr', driving_member='r1i1p1f1').to_dataset()
        ds_raws= cat.search(source='CRCM5-SN',driving_model='MPI-ESM1-2-LR', experiment='ssp370', variable='pr', driving_member='r1i1p1f1').to_dataset()
        ds_raw= xr.concat([ds_rawh, ds_raws], dim='time')


        ds = ds_raw.copy()
        ds=ds.convert_calendar('noleap')
        g=Grouper('time.dayofyear', window=31)
        
        groupby_obj =g.group(ds.pr.sel(time=slice('1991','2020')))
        
        q99 = groupby_obj.map(lambda x: quantile(x, [0.99], dim=['time', 'window']))
        q99=q99.rename({'dayofyear':'time'})

        #do one file per year
        for y in range(1950,2100):
            ds_cur= ds.sel(time=str(y))
            q99_cur=q99.copy()
            q99_cur['time']=ds_cur['time']
            out= ds_cur.where((ds_cur.pr > 10 *q99_cur).compute(), drop=True)
            xs.save_to_zarr(out, f"{CONFIG['paths']['tmpdir']}/q99_{y}.zarr",)


        # q99_repeated = xr.concat([q99] * 151, dim='dayofyear')
        # q99_repeated=q99_repeated.rename({'dayofyear':'time'})
        # q99_repeated['time']=ds['time']
        # # do one file per year
        # out= ds.pr.where((ds.pr > 10 *q99_repeated).compute(), drop=True)
        # xs.save_to_zarr(out, f"{CONFIG['paths']['tmpdir']}/q99.zarr",)

