
import xscen as xs
import xarray as xr
from xscen import CONFIG
import datetime
import numpy as np
import xsdba
from pathlib import Path
import xclim as xc
import glob
from xclim.indices.generic import     compare
from xclim.indices import run_length as rl
from xclim.core.units import convert_units_to, declare_units, to_agg_units

xs.load_config("../config/config_general.yml", "../config/config_region.yml", "../config/paths.yml")



if __name__ == '__main__':

    members=[]
    for s in ['ACCESS-CM2',
 'ACCESS-ESM1-5',
 'CMCC-ESM2',
 'CNRM-CM6-1',
 'CNRM-ESM2-1',
 'MIROC6',
 'MPI-ESM1-2-HR',
 'MPI-ESM1-2-LR',
 'MRI-ESM2-0']:
        print(s)
        f=glob.glob(f"{CONFIG['paths']['final']}/staging/simulation/biasadjusted/*/*/*/lait-E5L/*/{s}/ssp370/*/*/*/*")
        ds_E5L=xr.open_mfdataset(f, engine='zarr')
        ds_E5L['tasmax'] = xc.core.units.convert_units_to(ds_E5L['tasmax'], "degC")
        thi_E5L = ((1.8*ds_E5L['tasmax'] +32) - ((0.55-0.0055*ds_E5L['hursTasmax']) * (1.8*ds_E5L['tasmax']-26.8))).to_dataset(name='thi')
        thi_E5L.thi.attrs['units']='degC'


        
        f=glob.glob(f"{CONFIG['paths']['final']}/staging/simulation/biasadjusted/*/*/*/lait-C3/*/{s}/ssp370/*/*/*/*")
        ds_C3=xr.open_mfdataset(f, engine='zarr')
        ds_C3['tasmax'] = xc.core.units.convert_units_to(ds_C3['tasmax'], "degC")

        thi_C3 = ((1.8*ds_C3['tasmax'] +32) - ((0.55-0.0055*ds_C3['hursTasmax']) * (1.8*ds_C3['tasmax']-26.8))).to_dataset(name='thi')
        thi_C3.thi.attrs['units']='degC'

        thi_E5L = xs.regrid.regrid_dataset(thi_E5L, ds_grid=thi_C3, regridder_kwargs=dict(method='bilinear', reuse_weights=False))
        
        path=f"{CONFIG['indicators']}/{s}_E5L_thi.zarr.zip"
        if not Path(path).exists():
            xs.save_to_zarr(
                thi_E5L,
                path,
                zip_zarrdir= "${SLURM_TMPDIR}",
                )

        path=f"{CONFIG['indicators']}/{s}_C3_thi.zarr.zip"
        if not Path(path).exists():
            xs.save_to_zarr(
                thi_C3,
                path,
                zip_zarrdir= "${SLURM_TMPDIR}",
                )


        def thi_spell_total_length(
            thi: xr.DataArray,
            thresh: int = 65,
            window: int = 1,
            freq: str = "YS",
            op: str = ">=",
            resample_before_rl: bool = True,
        ) -> xr.DataArray:
            cond = compare(thi, op, thresh, constrain=(">", ">="))
            out = rl.resample_and_rl(
                cond,
                resample_before_rl,
                rl.windowed_run_count,
                window=window,
                freq=freq,
            )
            return to_agg_units(out, thi, "count")

        this_E5L=thi_spell_total_length(thi_E5L.thi).to_dataset(name='thi_spell_total_length')
        #put back nans
        this_E5L=this_E5L.where(~thi_E5L.thi.isel(time=0).isnull())

        path=f"{CONFIG['indicators']}/{s}_E5L_this.zarr.zip"
        if not Path(path).exists():
            xs.save_to_zarr(
                this_E5L,
                path,
                zip_zarrdir= "${SLURM_TMPDIR}",
                )

        this_C3=thi_spell_total_length(thi_C3.thi).to_dataset(name='thi_spell_total_length')
        #put back nans
        this_C3=this_C3.where(~thi_E5L.thi.isel(time=0).isnull())
        path=f"{CONFIG['indicators']}/{s}_C3_this.zarr.zip"
        if not Path(path).exists():
            xs.save_to_zarr(
                this_C3,
                path,
                zip_zarrdir= "${SLURM_TMPDIR}",
                )
        
