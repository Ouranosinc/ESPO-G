
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
import xsdba

xs.load_config("../config/ARCHES/config_Scaling.yml",  "../config/ARCHES/paths_Scaling.yml", reset=True)
cat = xs.ProjectCatalog(f'{CONFIG['paths']['final']}/cat_ARCHES.json')
cat_sim = xs.DataCatalog(CONFIG['extraction']['simulation']['search_data_catalogs']['data_catalogs'][0])
sftlf= cat_sim.search(source='CRCM5-SN', variable='sftlf',id='CMIP6_CORDEX_MPI-ESM1-2-LR_r1i1p1f1_OURANOS_CRCM5-SN_historical_r1_NAM-12' ).to_dataset(xarray_open_kwargs={'engine':'h5netcdf'})
mask = xs.regrid.create_mask(sftlf,**CONFIG["extraction"]["simulation"]["create_mask"],)


                
if not Path(f"{CONFIG['arches']}/correlogram").exists():
    Path(f"{CONFIG['arches']}/correlogram").mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':

    # NAM doesnt work with memory
    # reference
    ds = xr.open_zarr(f"{CONFIG['paths']['final']}/reference/NAM_CaSR_fullregion.zarr.zip")
    ds=xs.spatial.subset(ds, **CONFIG['diagregion']['Atlas'])
    ds= ds.sel(time=slice('1991','2020'))
    for var in ['pr','tasmin','tasmax']:
        path=f"{CONFIG['arches']}/correlogram/CaSR_atlas_correlogram-{var}.zarr.zip"
        if not Path(path).exists():
            out=xsdba.properties.spatial_correlogram(ds[var].compute(), dims=['rlat','rlon'], bins=300).to_dataset()
            out.attrs=ds.attrs
            xs.save_to_zarr(
                out,
                path,
                zip_zarrdir= "${SLURM_TMPDIR}",
                )
    
    # adjusted
    adj_dict=cat.search(source='CRCM5-SN', experiment='ssp370').to_dataset_dict()
    for sim_id, ds in adj_dict.items():
        dm=ds.attrs['cat:driving_model']
        mem=ds.attrs['cat:driving_member']
        baj=ds.attrs['cat:bias_adjust_project']
        ds=xs.spatial.subset(ds, **CONFIG['diagregion']['Atlas'])
        ds= ds.sel(time=slice('1991','2020'))
        for var in ['pr','tasmin','tasmax']:
            path=f"{CONFIG['arches']}/correlogram/{baj}_{dm}_{mem}_CRCM5-SN_ssp370_atlas_correlogram-{var}.zarr.zip"
            if not Path(path).exists():
                out=xsdba.properties.spatial_correlogram(ds[var].compute(), dims=['rlat','rlon'], bins=300).to_dataset()
                out.attrs=ds.attrs
                xs.save_to_zarr(
                    out,
                    path,
                    zip_zarrdir= "${SLURM_TMPDIR}",
                    )
        
        # associated raw

        ds_raw= cat_sim.search(
            driving_model=ds.attrs['cat:driving_model'],
            driving_member=ds.attrs['cat:driving_member'],
            source='CRCM5-SN',
            xrfreq='D',
            experiment='ssp370').to_dataset(xarray_open_kwargs={'engine':'h5netcdf'})
        ds_raw = ds_raw.where(mask)
        ds_raw=xs.spatial.subset(ds_raw,  **CONFIG['diagregion']['Atlas'])
        ds_raw= ds_raw.sel(time=slice('1991','2020'))
        for var in ['pr','tasmin','tasmax']:
            path=f"{CONFIG['arches']}/correlogram/raw_{dm}_{mem}_CRCM5-SN_ssp370_atlas_correlogram-{var}.zarr.zip"
            if not Path(path).exists():
                out=xsdba.properties.spatial_correlogram(ds_raw[var].compute(), dims=['rlat','rlon'], bins=300).to_dataset()
                out.attrs=ds_raw.attrs
                xs.save_to_zarr(
                    out,
                    path,
                    zip_zarrdir= "${SLURM_TMPDIR}",
                    )