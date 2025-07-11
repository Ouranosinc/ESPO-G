import xscen as xs
import xarray as xr
from xscen import CONFIG
import xclim as xc
import datetime
from dask.distributed import Client
import os
import sys
import time
from xclim.core.units import convert_units_to, declare_units, to_agg_units
from xclim.indices.generic import select_resample_op
from xclim.indices.generic import     compare
from xclim.core import Quantified
from xclim.indices import run_length as rl

xs.load_config("../config/config_general.yml", "../config/config_region.yml", "../config/paths.yml")

#brouillon
if __name__ == '__main__':
    pcat = xs.ProjectCatalog(f"{CONFIG['paths']['finaldir']}/compare-cat.json")
    client = Client(
        n_workers=2, threads_per_worker=1, memory_limit="250GB",
        local_directory=os.environ['SLURM_TMPDIR'],dashboard_address= 6785
    )

    #hx
    for i,ds in pcat.search(variable=['hursTasmax','tasmax']).to_dataset_dict().items():
        if pcat.exists_in_cat(variable='hx', id =ds.attrs['cat:id']):
            print(f"Skipping {ds.attrs['cat:id']} as hx already exists.")
            continue
        print(i,'hx')


        ds=ds.convert_calendar('noleap')
        ds=ds.sel(time=slice('1991','2020'))


        hx= xc.atmos.humidex(tas=ds.tasmax, hurs=ds.hursTasmax).to_dataset(name='hx')
        hx.attrs = ds.attrs
        hx.attrs['cat:variable'] = 'hx'
        hx.attrs['cat:xrfreq'] = 'D'
        hx.attrs['cat:format'] = 'zarr'

        # save
        path=f"{xs.build_path(hx, root=CONFIG['paths']['hx'])}.zip"
        
        xs.save_to_zarr(hx, path.replace('.zip', ''))
        xs.io.zip_directory(path.replace('.zip', ''), path, delete=True)

        pcat.update_from_ds(hx, path)

    #thi
    for i,ds in pcat.search(variable=['hursTasmax','tasmax']).to_dataset_dict().items():
        if pcat.exists_in_cat(variable='thi', id =ds.attrs['cat:id']):
            print(f"Skipping {ds.attrs['cat:id']} as thi already exists.")
            continue
        print(i)


        ds=ds.convert_calendar('noleap')
        ds=ds.sel(time=slice('1991','2020'))

        ds['tasmax'] = xc.core.units.convert_units_to(ds['tasmax'], "degC")
        ds['hursTasmax'] = xc.core.units.convert_units_to(ds['hursTasmax'], "%")
        thi = ((1.8*ds['tasmax'] +32) - ((0.55-0.0055*ds['hursTasmax']) * (1.8*ds['tasmax']-26.8))).to_dataset(name='thi')
        thi['thi'].attrs['units']=''

        thi.attrs = ds.attrs
        thi.attrs['cat:variable'] = 'thi'
        thi.attrs['cat:xrfreq'] = 'D'
        thi.attrs['cat:format'] = 'zarr'

        # save
        path=f"{xs.build_path(thi, root=CONFIG['paths']['hx'])}.zip"
        
        xs.save_to_zarr(thi, path.replace('.zip', ''))
        xs.io.zip_directory(path.replace('.zip', ''), path, delete=True)

        pcat.update_from_ds(thi, path)


    # hx days above
    for i,ds in pcat.search(variable=['hx']).to_dataset_dict().items():
        for N in [30,35]:
            if pcat.exists_in_cat(variable=f'hx{N}', id =ds.attrs['cat:id']):
                print(f"Skipping {ds.attrs['cat:id']} as hx{N} already exists.")
                continue
            print(i)

            def hx_days_above(
                hx,
                thresh,
                freq= "YS",
                op= ">",
            ):

                f = xc.indices.generic.threshold_count(hx, op, thresh, freq, constrain=(">", ">="))
                return xc.core.units.to_agg_units(f, hx, "count")

            hxN=hx_days_above(ds.hx, N).to_dataset(name=f'hx{N}')
            hxN.attrs = ds.attrs
            hxN.attrs['cat:variable'] = f'hx{N}'
            hxN.attrs['cat:format'] = 'zarr'

            print(hxN)
            # save
            path=f"{xs.build_path(hxN, root=CONFIG['paths']['hx'])}.zip"
            
            xs.save_to_zarr(hxN, path.replace('.zip', ''))
            xs.io.zip_directory(path.replace('.zip', ''), path, delete=True)

            pcat.update_from_ds(hxN, path)


    for i,ds in pcat.search(variable=['thi']).to_dataset_dict().items():
        if pcat.exists_in_cat(variable=f'thi_spell_total_length', id =ds.attrs['cat:id']):
            print(f"Skipping {ds.attrs['cat:id']} as this already exists.")
            continue
        print(i)

        def thi_spell_total_length(
            thi: xr.DataArray,
            thresh: int = 65,
            window: int = 8,
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

        this=thi_spell_total_length(ds.thi).to_dataset(name='thi_spell_total_length')
        this.attrs = ds.attrs
        this.attrs['cat:variable'] = 'thi_spell_total_length'
        this.attrs['cat:format'] = 'zarr'

        # save
        path=f"{xs.build_path(this, root=CONFIG['paths']['hx'])}.zip"
        
        xs.save_to_zarr(this, path.replace('.zip', ''))
        xs.io.zip_directory(path.replace('.zip', ''), path, delete=True)

        pcat.update_from_ds(this, path)