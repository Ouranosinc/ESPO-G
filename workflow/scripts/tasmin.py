from copy import deepcopy
import xscen as xs
import xclim as xc
import xarray as xr
import numpy as np
from datetime import datetime
xr.set_options(keep_attrs=True)
from workflow.scripts.utils import dask_cluster, save
from xscen.xclim_modules import conversions
from pathlib import Path
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    inputs=snakemake.input
    output=snakemake.output[0]
    config = deepcopy(snakemake.config)


    ds= xr.open_mfdataset(inputs, engine='zarr', decode_timedelta=False)

    # calculate tasmin back
    conv_mod= xs.indicators.load_xclim_module(Path(conversions.__file__).with_suffix(""))
    ds = ds.assign(tasmin=conv_mod.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax))
    ds['tasmin'].attrs['history'] = (f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Tasmin computed from tasmax and dtr.\n") + ds['tasmin'].attrs['history'] 



    ds = xs.clean_up(ds=ds,**config['clean_up']['xscen_clean_up']['tasmin'])
    # #TODO: check if it worked in yaml
    #ds.attrs['cat:domain'] = 'zarr'
    #ds.attrs['cat:_data_format_'] = 'zarr'
               
    chunks=xs.utils.translate_time_chunk(
        config['chunks']['final'],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,)
    
    

    xs.save_to_zarr(
        ds, 
        output, 
        **config['save_to_zarr'],
        rechunk=chunks
        )


