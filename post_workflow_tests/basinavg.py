
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
import geopandas as gpd
import pandas as pd
from shapely.geometry import box
xs.load_config( "paths_post-workflow.yml")




if __name__ == '__main__':

    lgdfs=[]
    files=glob.glob(f'{CONFIG['data']}/region_shapefiles/*.shp')
    for f in files:
        lgdfs.append(gpd.read_file(f))
    gdfsA= pd.concat(lgdfs)

    bbox = box(-83, 42, -55, 53)
    gdfs6=gpd.read_file(f'{CONFIG['data']}/hydrobasins/hybas_na_lev06_v1c.shp')
    gdfs6=gdfs6[gdfs6.geometry.within(bbox)] # in atlas region
    gdfs6=gdfs6[gdfs6['SUB_AREA']>200] # bigger than one grid point
    tol=0.01



    ds_ref = xr.open_zarr(f"{CONFIG['DQM-dtr']}/reference/NAM_CaSR_default.zarr.zip")
    ds_ref=ds_ref.chunk({"time": -1, "rlat":50, "rlon":50})
    for dm in ['MPI-ESM1-2-LR','CanESM5','NorESM2-MM']:
        ds_adj= xr.open_mfdataset(
                    glob.glob(f"{CONFIG['DQM-dtr']}/staging/simulation/biasadjusted/*_v20_CaSR/CMIP6/CORDEX/NAM/OURANOS/CRCM5-SN/{dm}/*/ssp370/r1/day/*/*.zarr.zip"),
                    engine='zarr')
        f= glob.glob(f"{CONFIG['regDQM-dtr']}/*_{dm}_*+extracted.zarr")[0]
        ds_ext=xr.open_zarr(f, decode_timedelta=False)
        for gdfs, geoname in zip([gdfsA, gdfs6], ['atlas', 'lev06']):
            print(geoname)
            for j in range(len(gdfs)):
                if not Path(f"{CONFIG['pathind']}/bilanpr/bassinextremes_{geoname}_{j}_{dm}.csv").exists():
                    print(j)
                    l=[]
                    for ds, method in zip([ds_ref, ds_adj, ds_ext], ['CaSR','adj','ext']):
                        print(method)
                        print(ds.coords)
                        #FIXME: until fixed in xscen
                        if 'crs' in ds:
                            ds=ds.rename({'crs':'rotated_pole'})
                            for var in ds.data_vars:
                                ds[var].attrs['grid_mapping']='rotated_pole'
                        print(ds.pr.attrs['grid_mapping'])
                        print(ds.coords)
                        cur=xs.spatial_mean(ds, method='xesmf', region=dict(name='tmp', method='shape',shape=gdfs.iloc[[j]]),simplify_tolerance=tol,
                                            kwargs={'skipna':True})
                        cur =cur.sel(time=slice('1991','2020'))
                        cur=cur.chunk({'time':-1})
                        
                        out=xc.atmos.max_n_day_precipitation_amount(ds=cur,window=5, freq='MS').to_dataset()
                        out=xs.utils.unstack_dates(out)
                        out= out.max('time')

                        q95=cur.groupby("time.month").quantile(0.95, skipna=True).pr
                        q95['month']=out['month']
                        out['q95pr']=q95
                        
                        df_cur=out.to_dataframe().reset_index()
                        df_cur['method']=method
                        l.append(df_cur)

                    df=pd.concat(l)
                    df.to_csv(f"{CONFIG['pathind']}/bilanpr/bassinextremes_{geoname}_{j}_{dm}.csv")


