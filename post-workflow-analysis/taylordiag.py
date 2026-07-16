
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
from copy import deepcopy

xs.load_config("../config/ARCHES/config_Scaling.yml",  "../config/ARCHES/paths_Scaling.yml", reset=True)
cat = xs.ProjectCatalog(f'{CONFIG['paths']['final']}/cat_ARCHES.json')
cat_sim = xs.DataCatalog(CONFIG['extraction']['simulation']['search_data_catalogs']['data_catalogs'][0])
sftlf= cat_sim.search(source='CRCM5-SN', variable='sftlf',id='CMIP6_CORDEX_MPI-ESM1-2-LR_r1i1p1f1_OURANOS_CRCM5-SN_historical_r1_NAM-12' ).to_dataset(xarray_open_kwargs={'engine':'h5netcdf'})
mask = xs.regrid.create_mask(sftlf, **CONFIG["extraction"]["simulation"]["create_mask"],)

if not Path(f"{CONFIG['arches']}/taylordiag").exists():
    Path(f"{CONFIG['arches']}/taylordiag").mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':

    variables=['tasmin','pr','tasmax', ]

    #SPATIAL
    for i,var in enumerate(variables):
        ds_ref = xr.open_zarr(f"{CONFIG['paths']['final']}/reference/NAM_CaSR_fullregion.zarr.zip")
        if var =='pr':
            with xr.set_options(keep_attrs=True):
                ds_ref['pr']=xc.core.units.convert_units_to(ds_ref['pr'], 'mm/day', context='hydro')
            ds_ref=ds_ref.sel(time=slice('1991','2020'))


        # adjusted
        adj_dict=cat.search(source='CRCM5-SN', experiment='ssp370', variable=var).to_dataset_dict()
        for sim_id, ds in adj_dict.items():
                if var =='pr':
                    with xr.set_options(keep_attrs=True):
                        ds['pr']=xc.core.units.convert_units_to(ds['pr'], 'mm/day', context='hydro')
                ds=ds.sel(time=slice('1991','2020'))

                dm=ds.attrs['cat:driving_model']
                mem=ds.attrs['cat:driving_member']
                baj=ds.attrs['cat:bias_adjust_project']


                # associated raw, regrid it.
                ds_raw= cat_sim.search(
                    driving_model=dm,
                    driving_member=mem,
                    variable=var,
                    xrfreq='D',
                    source='CRCM5-SN',
                    experiment='ssp370').to_dataset(xarray_open_kwargs={'engine':'h5netcdf'})


                ds_raw = ds_raw.where(mask)
                ds_input = ds_raw.drop_vars("crs", errors="ignore")
                # Adjust intermediate grids
                if "intermediate_grids" in CONFIG["regrid"]["regrid_dataset"]:
                    intermediate_grids = deepcopy(
                        CONFIG["regrid"]["regrid_dataset"]["intermediate_grids"]
                    )
                    grids = deepcopy(intermediate_grids)
                    est_res = xs.spatial._estimate_grid_resolution(ds_input)
                    for key, grid_info in grids.items():
                        if (
                            grid_info["cf_grid_2d"]["d_lon"] > est_res[0]
                            or grid_info["cf_grid_2d"]["d_lat"] > est_res[1]
                        ):
                            # Delete intermediate grids that are too coarse
                            intermediate_grids.pop(key)
                            print(
                                f"Pop grid {key} with resolution {grid_info['cf_grid_2d']['d_lon']}x{grid_info['cf_grid_2d']['d_lat']} because it is coarser than the estimated input grid resolution {est_res[0]}x{est_res[1]}"
                            )

                    if len(intermediate_grids) > 0:
                        CONFIG["regrid"]["regrid_dataset"]["intermediate_grids"] = (
                            intermediate_grids
                        )
                    else:
                        CONFIG["regrid"]["regrid_dataset"].pop("intermediate_grids")

                args=CONFIG["regrid"]["regrid_dataset"].copy()
                args['regridder_kwargs']['locstream_out']=False
                ds_reg = xs.regrid_dataset(
                    ds=ds_input, ds_grid=ds_ref, **args
                )

                
                if var =='pr':
                    with xr.set_options(keep_attrs=True):
                        ds_reg['pr']=xc.core.units.convert_units_to(ds_reg['pr'], 'mm/day', context='hydro')
                
                ds_reg=ds_reg.sel(time=slice('1991','2020'))
                
                
                path=f"{CONFIG['arches']}/taylordiag/{baj}_{dm}_{mem}_CRCM5-SN_ssp370_taylordiag-spatial-{var}.zarr.zip"
                if not Path(path).exists():
                    
                    out = xsdba.measures.taylordiagram(
                        ds[var].mean(dim='time', keep_attrs=True),
                        ds_reg[var].mean(dim='time', keep_attrs=True),
                         dim=['rlat', 'rlon']).to_dataset()
                    out.attrs=ds.attrs
                    xs.save_to_zarr(
                        out,
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )


                path=f"{CONFIG['arches']}/taylordiag/CaSR_{dm}_{mem}_CRCM5-SN_ssp370_taylordiag-spatial-{var}.zarr.zip"
                if not Path(path).exists():
                    out_ref = xsdba.measures.taylordiagram(
                        ds_ref[var].mean(dim='time', keep_attrs=True),
                        ds_reg[var].mean(dim='time', keep_attrs=True),
                        dim=['rlat', 'rlon']).to_dataset()
                    out_ref.attrs=ds_ref.attrs
                    xs.save_to_zarr(
                        out_ref,
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )

                
                path=f"{CONFIG['arches']}/taylordiag/{baj}_{dm}_{mem}_CRCM5-SN_ssp370_taylordiag-temporalJAN-{var}.zarr.zip"
                if not Path(path).exists():
                    ds_regJAN=xs.utils.unstack_dates(ds_reg)
                    ds_regJAN=ds_regJAN.sel(dayofyear=slice(None,31))

                    dsJAN=xs.utils.unstack_dates(ds)
                    dsJAN=dsJAN.sel(dayofyear=slice(None,31))
                    out = xsdba.measures.taylordiagram(dsJAN[var], ds_regJAN[var], dim=['dayofyear'])
                    out= out.where(~np.isinf(out)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True).to_dataset()
                    out.attrs=ds.attrs
                    xs.save_to_zarr(
                        out,
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )

                path=f"{CONFIG['arches']}/taylordiag/{baj}_{dm}_{mem}_CRCM5-SN_ssp370_taylordiag-temporalJUL-{var}.zarr.zip"
                if not Path(path).exists():
                    ds_regJUL=xs.utils.unstack_dates(ds_reg)
                    ds_regJUL=ds_regJUL.sel(dayofyear=slice(183,213))

                    dsJUL=xs.utils.unstack_dates(ds)
                    dsJUL=dsJUL.sel(dayofyear=slice(183,213))
                    out = xsdba.measures.taylordiagram(dsJUL[var], ds_regJUL[var], dim=['dayofyear'])
                    out= out.where(~np.isinf(out)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True).to_dataset()
                    out.attrs=ds.attrs
                    xs.save_to_zarr(
                        out,
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )

                path=f"{CONFIG['arches']}/taylordiag/CaSR_{dm}_{mem}_CRCM5-SN_ssp370_taylordiag-temporalJAN-{var}.zarr.zip"
                if not Path(path).exists():
                    ds_regJAN=xs.utils.unstack_dates(ds_reg)
                    ds_regJAN=ds_regJAN.sel(dayofyear=slice(None,31))

                    ds_refJAN=xs.utils.unstack_dates(ds_ref)
                    ds_refJAN=ds_refJAN.sel(dayofyear=slice(None,31))
                    out = xsdba.measures.taylordiagram(ds_refJAN[var], ds_regJAN[var], dim=['dayofyear'])
                    out= out.where(~np.isinf(out)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True).to_dataset()
                    out.attrs=ds_ref.attrs
                    xs.save_to_zarr(
                        out,
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )

                path=f"{CONFIG['arches']}/taylordiag/CaSR_{dm}_{mem}_CRCM5-SN_ssp370_taylordiag-temporalJUL-{var}.zarr.zip"
                if not Path(path).exists():
                    ds_regJUL=xs.utils.unstack_dates(ds_reg)
                    ds_regJUL=ds_regJUL.sel(dayofyear=slice(183,213))

                    ds_refJUL=xs.utils.unstack_dates(ds_ref)
                    ds_refJUL=ds_refJUL.sel(dayofyear=slice(183,213))
                    out = xsdba.measures.taylordiagram(ds_refJUL[var], ds_regJUL[var], dim=['dayofyear'])
                    out= out.where(~np.isinf(out)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True).to_dataset()
                    out.attrs=ds_ref.attrs
                    xs.save_to_zarr(
                        out,
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        )
                       
                


    # # TEMPORAL
    # for i,var in enumerate(variables):
    #     ds_ref=xr.open_zarr(f"{CONFIG['DQM']}/reference/NAM_CaSR_default.zarr.zip", decode_timedelta=False)
    #     ds_ref=ds_ref.sel(time=slice('1991','2020'))
    #     if var =='pr':
    #         with xr.set_options(keep_attrs=True):
    #             ds_ref['pr']=xc.core.units.convert_units_to(ds_ref['pr'], 'mm/day', context='hydro')
    #     ds_ref=xs.utils.unstack_dates(ds_ref)
    #     ds_refJAN=ds_ref.sel(dayofyear=slice(None,31))
    #     ds_refJUL=ds_ref.sel(dayofyear=slice(183,213))
        
    #     for dm in dms:
    #         dreg=[]
    #         for i in range(6):
    #             print(i)
    #             dreg.append(xr.open_zarr(glob.glob(f"{CONFIG['regDQM']}/CMIP6_CORDEX_{dm}_*sr-{i}+regridded.zarr")[0]))
    #         ds_reg=xr.concat(dreg, dim='loc')
    #         ds_reg=xs.utils.unstack_fill_nan(ds_reg, coords= f"{CONFIG['DQM']}"+"/coords/coords_{domain}_{shape}.nc")
    #         ds_reg=ds_reg.sel(time=slice('1991','2020'))
    #         if var =='pr':
    #             with xr.set_options(keep_attrs=True):
    #                 ds_reg['pr']=xc.core.units.convert_units_to(ds_reg['pr'], 'mm/day', context='hydro')
            
    #         ds_reg=xs.utils.unstack_dates(ds_reg)
    #         ds_regJAN=ds_reg.sel(dayofyear=slice(None,31))
    #         ds_regJUL=ds_reg.sel(dayofyear=slice(183,213))
    #         print('reg done')
            

    #         path=f"{CONFIG['pathind']}/CaSR_{dm}_timetaylordiagJAN-{var}.zarr.zip"
    #         if not Path(path).exists():
    #             out_ref = xsdba.measures.taylordiagram(ds_refJAN[var], ds_regJAN[var], dim=['dayofyear'])
    #             xs.save_to_zarr(
    #                 out_ref.to_dataset(),
    #                 f"{CONFIG['pathind']}/CaSR_{dm}_timetaylordiagJAN-{var}_complete.zarr.zip",
    #                 rechunk={'time':-1,'rlat':-1, 'rlon':-1,'taylor_param':1},
    #                 zip_zarrdir= "${SLURM_TMPDIR}",
    #                 )
    #             out_ref= out_ref.where(~np.isinf(out_ref)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True)
    #             xs.save_to_zarr(
    #                 out_ref.to_dataset(),
    #                 path,
    #                 zip_zarrdir= "${SLURM_TMPDIR}",
    #                 )

    #         path=f"{CONFIG['pathind']}/CaSR_{dm}_timetaylordiagJUL-{var}.zarr.zip"
    #         if not Path(path).exists():
    #             out_ref = xsdba.measures.taylordiagram(ds_refJUL[var], ds_regJUL[var], dim=['dayofyear'])
    #             xs.save_to_zarr(
    #                 out_ref.to_dataset(),
    #                 f"{CONFIG['pathind']}/CaSR_{dm}_timetaylordiagJUL-{var}_complete.zarr.zip",
    #                 rechunk={'time':-1,'rlat':-1, 'rlon':-1,'taylor_param':1},
    #                 zip_zarrdir= "${SLURM_TMPDIR}",
    #                 )
    #             out_ref= out_ref.where(~np.isinf(out_ref)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True)
    #             print('taylor done  ')
    #             xs.save_to_zarr(
    #                 out_ref.to_dataset(),
    #                 path,
    #                 zip_zarrdir= "${SLURM_TMPDIR}",
    #                 )
            
    #         for j,m in enumerate(name_methods,1):
    #             f= glob.glob(f"{CONFIG[m]}/*/*/*/*/*/*/*/*/*/{dm}/*/*/*/*/{var}/*")[0]
    #             ds=xr.open_zarr(f, decode_timedelta=False)
    #             ds=ds.sel(time=slice('1991','2020'))
    #             if var =='pr':
    #                 with xr.set_options(keep_attrs=True):
    #                     ds['pr']=xc.core.units.convert_units_to(ds['pr'], 'mm/day', context='hydro')
    #             ds=xs.utils.unstack_dates(ds)
    #             dsJAN=ds.sel(dayofyear=slice(None,31))
    #             dsJUL=ds.sel(dayofyear=slice(183,213))
                
    #             path=f"{CONFIG['pathind']}/{m}_{dm}_timetaylordiagJAN-{var}.zarr.zip"
    #             if not Path(path).exists():
    #                 out = xsdba.measures.taylordiagram(dsJAN[var], ds_regJAN[var], dim=['dayofyear'])
    #                 xs.save_to_zarr(
    #                     out.to_dataset(),
    #                     f"{CONFIG['pathind']}/{m}_{dm}_timetaylordiagJAN-{var}_complete.zarr.zip",
    #                     rechunk={'time':-1,'rlat':-1, 'rlon':-1,'taylor_param':1},
    #                     zip_zarrdir= "${SLURM_TMPDIR}",
    #                     )
    #                 out= out.where(~np.isinf(out)).mean(dim=['rlat', 'rlon', 'time'], keep_attrs=True)
    #                 xs.save_to_zarr(
    #                     out.to_dataset(),
    #                     path,
    #                     zip_zarrdir= "${SLURM_TMPDIR}",
    #                     )


    #             path=f"{CONFIG['pathind']}/{m}_{dm}_timetaylordiagJUL-{var}.zarr.zip"
    #             if not Path(path).exists():
    #                 out = xsdba.measures.taylordiagram(dsJUL[var], ds_regJUL[var], dim=['dayofyear'])
    #                 xs.save_to_zarr(
    #                     out.to_dataset(),
    #                     f"{CONFIG['pathind']}/{m}_{dm}_timetaylordiagJUL-{var}_complete.zarr.zip",
    #                     rechunk={'time':-1,'rlat':-1, 'rlon':-1,'taylor_param':1},
    #                     zip_zarrdir= "${SLURM_TMPDIR}",
    #                     )
    #                 out= out.where(~np.isinf(out)).mean(dim=['rlat', 'rlon', 'time'])
    #                 xs.save_to_zarr(
    #                     out.to_dataset(),
    #                     path,
    #                     zip_zarrdir= "${SLURM_TMPDIR}",
    #                     )