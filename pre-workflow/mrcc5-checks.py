
import xscen as xs
import xarray as xr
from xscen import CONFIG
import xclim as xc
import datetime
from dask.distributed import Client
import os
import sys
import time

xs.load_config("../config/config_general.yml", "../config/config_region.yml", "../config/paths.yml")


if __name__ == '__main__':
    cat=xs.DataCatalog(CONFIG['extraction']['simulation']['search_data_catalogs']['data_catalogs'][0])
    # d=cat.search(source='CRCM5-SN', xrfreq='D',
    #             variable=['pr', 'tasmax', 'tasmin'], experiment='ssp*',
    #             ).to_dataset_dict(xarray_open_kwargs={'engine':'h5netcdf'})
    # for i, ds in d.items():
    #     print(i)
    #     if 'CanESM5' in i:
    #         ds=ds.sel(time=slice('2015-01-02', None))
    #         print("ds=ds.sel(time=slice('2015-01-02', None))")
    #     if 'MPI' in i:
    #         ds=ds.sel(time=slice('2015-01-02', None))
    #         print("ds=ds.sel(time=slice('2015-01-02', None))")
    #     for var in ds.data_vars:
    #         print(var)
    #         print(ds[var].isnull().sum().values)

    # d=cat.search(source='CRCM5-SN', xrfreq='D',
    #             variable=['pr', 'tasmax', 'tasmin'], experiment='historical',
    #             ).to_dataset_dict(xarray_open_kwargs={'engine':'h5netcdf'})
    # for i, ds in d.items():
    #     print(i)
    #     if 'CNRM' in i:
    #         ds.loc[dict(time="1950-01-01")] = 999
    #         ds.loc[dict(time=slice("1955-04-21","1955-04-30"))] = 999
    #         ds.loc[dict(time=slice("2002-04-19","2002-04-30"))] = 999
    #         ds.loc[dict(time=slice("2009-02-13","2009-02-28"))] = 999
    #         print("cnrm removed dates")

    #     for var in ds.data_vars:
    #         print(var)
    #         print(ds[var].isnull().sum().values)
    d=cat.search(source='CRCM5-SN', xrfreq='D',
                variable=['pr', 'tasmax', 'tasmin'],
                ).to_dataset_dict(xarray_open_kwargs={'engine':'h5netcdf'})
    for i, ds in d.items():
        print(i)
        for var in ds.data_vars:
            print(var)
            print(ds[var].min().values, ds[var].max().values)