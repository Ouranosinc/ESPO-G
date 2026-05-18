
import xscen as xs
import xarray as xr
from xscen import CONFIG
import xclim as xc
import datetime
from dask.distributed import Client
import os
import sys
import time

xs.load_config("../config/config_ESPO-G.yml",  "../config/paths_ESPO-G.yml")


if __name__ == '__main__':

    # search cat
    cat_sim_id = xs.search_data_catalogs(**CONFIG['extraction']['simulation']['search_data_catalogs'],)

    for sim_id, dc_id in cat_sim_id.items():
        print(sim_id, )

        ds = xs.extract_dataset(catalog=dc_id,
                                    region=CONFIG['full_region'],
                                    **CONFIG['extraction']['simulation']['extract_dataset'],
                                    )['D']

        hc = xs.diagnostics.health_checks(
        ds=ds,
        **CONFIG['health_checks']['extract'])

        hc.attrs.update(ds.attrs)

        xs.save_to_zarr(hc,
         f"{CONFIG['paths']['output']}/inputchecks/{sim_id}_inputchecks.zarr.zip",
          **CONFIG['save_to_zarr'])
    # for i, ds in d.items():
    #     print(i)
    #     for var in ds.data_vars:
    #         print(var)
    #         print(ds[var].min().values, ds[var].max().values)