import os
import xarray as xr
import xscen as xs
from xscen import CONFIG
from xscen.xclim_modules import conversions
from workflow.scripts.utils import create_tmp_path
from pathlib import Path
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml","config/config_region.yml","config/paths.yml")

if __name__ == '__main__':

    list_dsR = []
    for file in snakemake.input:  # type: ignore
        dsR = xr.open_zarr(file, decode_timedelta=False)
        dsR.lat.encoding.pop('chunks', None)
        dsR.lon.encoding.pop('chunks', None)
        list_dsR.append(dsR)

    ds= xr.concat(list_dsR, 'loc')

    conv_mod= xs.indicators.load_xclim_module(Path(conversions.__file__).with_suffix(""))

    if 'tasmin' not in ds and 'dtr' in ds:
        ds['tasmin']=conv_mod.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax)
    elif 'dtr' not in ds and 'tasmin' in ds:
        ds['dtr']=conv_mod.dtr_from_minmax(tasmin=ds.tasmin, tasmax=ds.tasmax)


    ds = xs.clean_up(ds = ds.chunk({'time':-1}),
                    **CONFIG['clean_up']['xscen_clean_up'])
    
    # eventually put un clean up
    ds.attrs['cat:domain'] = CONFIG['full_region']['name']
    ds.attrs.pop('cat:path', None)

    for var in ds.data_vars:
        ds_cur=ds[[var]]
        clean_path=f"{os.environ['SLURM_TMPDIR']}/{snakemake.wildcards.sim_id}_{snakemake.wildcards.dom}_{var}_cleaned.zarr"
        chunks=xs.utils.translate_time_chunk(
            CONFIG['chunks']['final'],
            calendar=ds_cur.time.dt.calendar,
            timesize=ds_cur.time.size,)
        ds_cur=ds_cur.chunk(chunks)

        xs.save_to_zarr(ds_cur,snakemake.output[var], **CONFIG['clean_up']['save'])

