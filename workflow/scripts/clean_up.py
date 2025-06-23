import xscen as xs
import xarray as xr
from xscen import CONFIG
import numpy as np
xr.set_options(keep_attrs=True)
from workflow.scripts.utils import dask_cluster
from xscen.xclim_modules import conversions
from pathlib import Path
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

if __name__ == '__main__':
    
    # get all adjusted data
    ds = xr.open_mfdataset(snakemake.input, engine='zarr', decode_timedelta=False)

    conv_mod= xs.indicators.load_xclim_module(Path(conversions.__file__).with_suffix(""))
    ds = ds.assign(tasmin=conv_mod.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax))

    ds = xs.clean_up(ds=ds,**CONFIG['clean_up']['xscen_clean_up'])

    ds.attrs['cat:_data_format_'] = 'zarr'
    ds.attrs['cat:date'] = 'zarr'


    chunks=xs.utils.translate_time_chunk(
        CONFIG['chunks']['final'],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,)
    ds=ds.chunk(chunks)

    xs.save_to_zarr(ds, snakemake.output[0], itervar=True, **CONFIG['clean_up']['save'])
