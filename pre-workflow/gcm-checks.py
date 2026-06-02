
import xscen as xs
import xarray as xr
from xscen import CONFIG
import xclim as xc
import datetime
from dask.distributed import Client
import os
import sys
import time
from pathlib import Path

xs.load_config("../config/config_ESPO-G.yml",  "../config/paths_ESPO-G.yml")


if __name__ == '__main__':

    # search cat
    cat_sim_id = xs.search_data_catalogs(**CONFIG['extraction']['simulation']['search_data_catalogs'],)

    for sim_id, dc_id in cat_sim_id.items():
        path=f"{CONFIG['paths']['final']}/inputchecks/{sim_id}_inputchecks.zarr.zip"
        if not Path(path).exists():
            print(sim_id, )

            ds = xs.extract_dataset(catalog=dc_id,
                                        region=CONFIG['full_region'],
                                        **CONFIG['extraction']['simulation']['extract_dataset'],
                                        )['D']

            hc = xs.diagnostics.health_checks(
            ds=ds,
            **CONFIG['health_checks']['extract'])

            hc.attrs.update(ds.attrs)
            for var in hc.data_vars:
                if hc[var].values:
                    if var == 'pr_very_large_precipitation_events':
                        ma=ds.pr.max(keep_attrs=True).values
                        mm=xc.core.units.convert_units_to(f"{ma} kg m-2 s-1", 'mm/day', context='hydro')
                        print('max pr', ma, 'kg m-2 s-1', mm, 'mm/day'  )

                    if var == 'tasmin_temperature_extremely_low':
                        mi=ds.tasmin.min().values
                        mm=xc.core.units.convert_units_to(f"{mi} K", 'degC')
                        print('min tasmin', mi, 'K', mm, 'degC'  )
                    if var =='tasmax_temperature_extremely_high':
                        ma=ds.tasmax.max().values
                        mm=xc.core.units.convert_units_to(f"{ma} K", 'degC')
                        print('max tasmax', ma, 'K', mm, 'degC'  )

            xs.save_to_zarr(hc,
            path,
            **CONFIG['save_to_zarr'])
        # for i, ds in d.items():
        #     print(i)
        #     for var in ds.data_vars:
        #         print(var)
        #         print(ds[var].min().values, ds[var].max().values)