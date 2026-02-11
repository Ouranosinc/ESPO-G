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
import pandas as pd
import numpy as np

xs.load_config("../config/config_ESPO-R-DQM.yml", "../config/paths_ESPO-R-DQM.yml")
cat=xs.DataCatalog(CONFIG['extraction']['simulation']['search_data_catalogs']['data_catalogs'][0])

catr=xs.DataCatalog(CONFIG['extraction']['reference']['CaSR']['search_data_catalogs']['data_catalogs'][0])


if __name__ == '__main__':

    with Client(
            n_workers=4, memory_limit="100GB",
            dashboard_address= 6788,
            local_directory=os.environ['SLURM_TMPDIR'],
        ):


        # reg
        for sr in range(6):
            print(sr)
            ds_reg= xr.open_zarr(f"{CONFIG['paths']['tmpdir']}/CMIP6_CORDEX_NorESM2-MM_r1i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12+NAM+CaSR+sr-{sr}+regridded.zarr")
            ds_reg=ds_reg.convert_calendar('noleap')
            ds_reg_clim=ds_reg.sel(time=slice('1991','2020')).chunk({'time':-1, 'loc':50})
            g=Grouper('time.dayofyear', window=31)
            
            groupby_obj_reg =g.group(ds_reg_clim.pr)
            
            q99_reg = groupby_obj_reg.map(lambda x: quantile(x, [0.99], dim=['time', 'window']))
            q99_reg=q99_reg.to_dataset(name='pr')
            q99_reg=q99_reg.chunk({'dayofyear':-1, 'loc':50})
            print(q99_reg)
            for v in q99_reg.coords:
                if 'chunks' in q99_reg[v].encoding:
                    del q99_reg[v].encoding['chunks']
            xs.save_to_zarr(q99_reg, f"{CONFIG['paths']['tmpdir']}/q99/NorESM2-MM_q99_climreg{sr}.zarr.zip",
                zip_zarrdir= '${SLURM_TMPDIR}'
                )




    #where are all the pr above 10 q99 on reg
    count=[]
    for i in range(6):
        q99= xr.open_zarr(f"{CONFIG['regDQM']}/q99/NorESM2-MM_q99_climreg{i}.zarr.zip")
        ds= xr.open_zarr(f"{CONFIG['regDQM']}/CMIP6_CORDEX_NorESM2-MM_r1i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12+NAM+CaSR+sr-{i}+regridded.zarr")
        ds=ds.convert_calendar('noleap')
        q99=q99.rename({'dayofyear':'time'})


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
        dftot=pd.concat(d)
        dftot.to_csv(f"{CONFIG['regDQM']}/q99/NorESM2-MM_1000q99reg-{i}.csv")
        

    print(np.sum(count))



    # #if True:

    #     #ds_rawh= cat.search(source='CRCM5-SN',driving_model='MPI-ESM1-2-LR', experiment='historical', variable='pr', driving_member='r1i1p1f1').to_dataset()
    #     #ds_raws= cat.search(source='CRCM5-SN',driving_model='MPI-ESM1-2-LR', experiment='ssp370', variable='pr', driving_member='r1i1p1f1').to_dataset()
    #     #ds_raw= xr.concat([ds_rawh, ds_raws], dim='time')


    #     # # sim
    #     # ds = ds_raw.copy()
    #     # ds=ds.convert_calendar('noleap')
    #     # ds_clim=ds.sel(time=slice('1991','2020')).chunk({'time':-1, 'rlat':50, 'rlon':50})
    #     # g=Grouper('time.dayofyear', window=31)
        
    #     # groupby_obj =g.group(ds_clim.pr)
        
    #     # q99 = groupby_obj.map(lambda x: quantile(x, [0.99], dim=['time', 'window']))
    #     # q99=q99.to_dataset(name='pr')
    #     # q99=q99.chunk({'dayofyear':-1, 'rlat':50, 'rlon':50})
    #     # print(q99)
    #     # xs.save_to_zarr(q99, f"{CONFIG['paths']['tmpdir']}/q99/q99_clim.zarr.zip",
    #     #     zip_zarrdir= '${SLURM_TMPDIR}'
    #     #     )
        #     # q99= xr.open_zarr(f"{CONFIG['paths']['tmpdir']}/q99/q99_clim.zarr.zip", decode_timedelta=False).pr
    #     # q99=q99.rename({'dayofyear':'time'})

    #     #do one file per year
    #     #for y in range(1950,2101):
    #     # for y in range(2100,2101):
    #     #     print(y)
    #     #     ds_cur= ds.sel(time=str(y))
    #     #     print(ds_cur)
    #     #     q99_cur=q99.copy()
    #     #     q99_cur['time']=ds_cur['time']
    #     #     q99_cur=q99_cur.squeeze().drop_vars('quantiles')
    #     #     print(q99_cur)
    #     #     out= ds_cur.where((ds_cur.pr > 10 *q99_cur).compute(), drop=True)
    #     #     out=out.chunk({'time':-1, 'rlat':50, 'rlon':50})
    #     #     print(out)
    #     #     xs.save_to_zarr(out, f"{CONFIG['paths']['tmpdir']}/q99/q99_{y}.zarr.zip",
    #     #     zip_zarrdir= '${SLURM_TMPDIR}'
    #     #     )
