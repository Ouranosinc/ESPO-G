
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
import xsdba

xs.load_config( "paths_post-workflow.yml")


if __name__ == '__main__':

    name_methods={'Scaling':'Scaling-dtr','tasmin':'DQM-tasmin','DQM':'DQM-dtr'}
    dms=['MPI-ESM1-2-LR','CanESM5','NorESM2-MM']
    variables=['tasmin','pr','tasmax', ]

    # SPATIAL
    # for i,var in enumerate(variables):
    #     ds_ref=xr.open_zarr(f"{CONFIG['DQM']}/reference/NAM_CaSR_default.zarr.zip", decode_timedelta=False)
    #     ds_ref=ds_ref.sel(time=slice('1991','2020')).mean(dim='time', keep_attrs=True)
    #     if var =='pr':
    #         with xr.set_options(keep_attrs=True):
    #             ds_ref['pr']=xc.core.units.convert_units_to(ds_ref['pr'], 'mm/day', context='hydro')

        
    #     for dm in dms:
    #         dreg=[]
    #         for i in range(6):
    #             dreg.append(xr.open_zarr(glob.glob(f"{CONFIG['regDQM']}/CMIP6_CORDEX_{dm}_*sr-{i}+regridded.zarr")[0]))
    #         ds_reg=xr.concat(dreg, dim='loc')
    #         ds_reg=xs.utils.unstack_fill_nan(ds_reg, coords= f"{CONFIG['DQM']}"+"/coords/coords_{domain}_{shape}.nc")
    #         ds_reg=ds_reg.sel(time=slice('1991','2020')).mean(dim='time', keep_attrs=True)
    #         if var =='pr':
    #             with xr.set_options(keep_attrs=True):
    #                 ds_reg['pr']=xc.core.units.convert_units_to(ds_reg['pr'], 'mm/day', context='hydro')
            

    #         path=f"{CONFIG['pathind']}/CaSR_{dm}_taylordiag-{var}.zarr.zip"
    #         if not Path(path).exists():
    #             out_ref = xsdba.measures.taylordiagram(ds_ref[var], ds_reg[var], dim=['rlat', 'rlon'])
    #             xs.save_to_zarr(
    #                 out_ref.to_dataset(),
    #                 path,
    #                 zip_zarrdir= "${SLURM_TMPDIR}",
    #                 )
            
    #         for j,m in enumerate(name_methods,1):
    #             f= glob.glob(f"{CONFIG[m]}/*/*/*/*/*/*/*/*/*/{dm}/*/*/*/*/{var}/*")[0]
    #             ds=xr.open_zarr(f, decode_timedelta=False)
    #             ds=ds.sel(time=slice('1991','2020')).mean(dim='time', keep_attrs=True)
    #             if var =='pr':
    #                 with xr.set_options(keep_attrs=True):
    #                     ds['pr']=xc.core.units.convert_units_to(ds['pr'], 'mm/day', context='hydro')

    #             path=f"{CONFIG['pathind']}/{m}_{dm}_taylordiag-{var}.zarr.zip"
    #             if not Path(path).exists():
    #                 out = xsdba.measures.taylordiagram(ds[var], ds_reg[var], dim=['rlat', 'rlon'])
    #                 xs.save_to_zarr(
    #                     out.to_dataset(),
    #                     path,
    #                     zip_zarrdir= "${SLURM_TMPDIR}",
    #                     )


    # TEMPORAL
    for i,var in enumerate(variables):
        ds_ref=xr.open_zarr(f"{CONFIG['DQM']}/reference/NAM_CaSR_default.zarr.zip", decode_timedelta=False)
        ds_ref=ds_ref.sel(time=slice('1991','2020'))
        if var =='pr':
            with xr.set_options(keep_attrs=True):
                ds_ref['pr']=xc.core.units.convert_units_to(ds_ref['pr'], 'mm/day', context='hydro')
        ds_ref=xs.utils.unstack_dates(ds_ref)
        ds_refJAN=ds_ref.sel(dayofyear=slice(None,31))
        ds_refJUL=ds_ref.sel(dayofyear=slice(183,213))
        
        for dm in dms:
            dreg=[]
            for i in range(6):
                print(i)
                dreg.append(xr.open_zarr(glob.glob(f"{CONFIG['regDQM']}/CMIP6_CORDEX_{dm}_*sr-{i}+regridded.zarr")[0]))
            ds_reg=xr.concat(dreg, dim='loc')
            ds_reg=xs.utils.unstack_fill_nan(ds_reg, coords= f"{CONFIG['DQM']}"+"/coords/coords_{domain}_{shape}.nc")
            ds_reg=ds_reg.sel(time=slice('1991','2020'))
            if var =='pr':
                with xr.set_options(keep_attrs=True):
                    ds_reg['pr']=xc.core.units.convert_units_to(ds_reg['pr'], 'mm/day', context='hydro')
            
            ds_reg=xs.utils.unstack_dates(ds_reg)
            ds_regJAN=ds_reg.sel(dayofyear=slice(None,31))
            ds_regJUL=ds_reg.sel(dayofyear=slice(183,213))
            print('reg done')
            

            path=f"{CONFIG['pathind']}/CaSR_{dm}_timetaylordiagJAN-{var}.zarr.zip"
            if not Path(path).exists():
                out_ref = xsdba.measures.taylordiagram(ds_refJAN[var], ds_regJAN[var], dim=['dayofyear'])
                xs.save_to_zarr(
                    out_ref.to_dataset(),
                    f"{CONFIG['pathind']}/CaSR_{dm}_timetaylordiagJAN-{var}_complete.zarr.zip",
                    rechunk={'time':-1,'rlat':-1, 'rlon':-1,'taylor_param':1},
                    zip_zarrdir= "${SLURM_TMPDIR}",
                    )
                out_ref= out_ref.where(~np.isinf(out_ref)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True)
                xs.save_to_zarr(
                    out_ref.to_dataset(),
                    path,
                    zip_zarrdir= "${SLURM_TMPDIR}",
                    )

            path=f"{CONFIG['pathind']}/CaSR_{dm}_timetaylordiagJUL-{var}.zarr.zip"
            if not Path(path).exists():
                out_ref = xsdba.measures.taylordiagram(ds_refJUL[var], ds_regJUL[var], dim=['dayofyear'])
                xs.save_to_zarr(
                    out_ref.to_dataset(),
                    f"{CONFIG['pathind']}/CaSR_{dm}_timetaylordiagJUL-{var}_complete.zarr.zip",
                    rechunk={'time':-1,'rlat':-1, 'rlon':-1,'taylor_param':1},
                    zip_zarrdir= "${SLURM_TMPDIR}",
                    )
                out_ref= out_ref.where(~np.isinf(out_ref)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True)
                print('taylor done  ')
                xs.save_to_zarr(
                    out_ref.to_dataset(),
                    path,
                    zip_zarrdir= "${SLURM_TMPDIR}",
                    )
            
            for j,m in enumerate(name_methods,1):
                f= glob.glob(f"{CONFIG[m]}/*/*/*/*/*/*/*/*/*/{dm}/*/*/*/*/{var}/*")[0]
                ds=xr.open_zarr(f, decode_timedelta=False)
                ds=ds.sel(time=slice('1991','2020'))
                if var =='pr':
                    with xr.set_options(keep_attrs=True):
                        ds['pr']=xc.core.units.convert_units_to(ds['pr'], 'mm/day', context='hydro')
                ds=xs.utils.unstack_dates(ds)
                dsJAN=ds.sel(dayofyear=slice(None,31))
                dsJUL=ds.sel(dayofyear=slice(183,213))
                
                path=f"{CONFIG['pathind']}/{m}_{dm}_timetaylordiagJAN-{var}.zarr.zip"
                if not Path(path).exists():
                    out = xsdba.measures.taylordiagram(dsJAN[var], ds_regJAN[var], dim=['dayofyear'])
                    xs.save_to_zarr(
                        out.to_dataset(),
                        f"{CONFIG['pathind']}/{m}_{dm}_timetaylordiagJAN-{var}_complete.zarr.zip",
                        rechunk={'time':-1,'rlat':-1, 'rlon':-1,'taylor_param':1},
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )
                    out= out.where(~np.isinf(out)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True)
                    xs.save_to_zarr(
                        out.to_dataset(),
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )


                path=f"{CONFIG['pathind']}/{m}_{dm}_timetaylordiagJUL-{var}.zarr.zip"
                if not Path(path).exists():
                    out = xsdba.measures.taylordiagram(dsJUL[var], ds_regJUL[var], dim=['dayofyear'])
                    xs.save_to_zarr(
                        out.to_dataset(),
                        f"{CONFIG['pathind']}/{m}_{dm}_timetaylordiagJUL-{var}_complete.zarr.zip",
                        rechunk={'time':-1,'rlat':-1, 'rlon':-1,'taylor_param':1},
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )
                    out= out.where(~np.isinf(out)).mean(dim=['rlat', 'rlon', 'time'])
                    xs.save_to_zarr(
                        out.to_dataset(),
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )