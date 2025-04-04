import os
import xarray as xr
import xscen as xs
from xscen import CONFIG
from xscen.xclim_modules import conversions
from workflow.scripts.utils import create_tmp_path

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    list_dsR = []
    for file in snakemake.input:  # type: ignore
        dsR = xr.open_zarr(file, decode_timedelta=False)
        dsR.lat.encoding.pop('chunks', None)
        dsR.lon.encoding.pop('chunks', None)
        list_dsR.append(dsR)

    ds= xr.concat(list_dsR, 'loc')

    if 'tasmin' not in ds:
        ds['tasmin']=conversions.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax)
    elif 'dtr' not in ds:
        ds['dtr']=conversions.dtr_from_minmax(tasmin=ds.tasmin, tasmax=ds.tasmax)


    ds = xs.clean_up(ds = ds.chunk({'time':-1}),
                    **CONFIG['clean_up']['xscen_clean_up'])
    
    # eventually put un clean up
    ds.attrs['cat:domain'] = CONFIG['custom']['full_region']['name']
    ds.attrs.pop('cat:path', None)

    for var in ds.data_vars:
        ds_cur=ds[[var]]
        clean_path=f"{os.environ['SLURM_TMPDIR']}/{snakemake.wildcards.sim_id}_{snakemake.wildcards.dom}_{var}_cleaned.zarr"
        xs.save_to_zarr(ds_cur, clean_path)
        
        rechunk_path= create_tmp_path(snakemake.output[var])
        xs.io.rechunk(
            path_in=clean_path,
            path_out=rechunk_path,
            chunks_over_dim=CONFIG['chunks']['final'],
            temp_store=f"{os.environ['SLURM_TMPDIR']}/tmp_rechunk/{snakemake.wildcards.sim_id}/",
            **CONFIG['rechunk'],
            overwrite=True)
        
        xs.io.zip_directory( rechunk_path,snakemake.output[var])
