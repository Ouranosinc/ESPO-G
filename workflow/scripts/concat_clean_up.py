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
    var=snakemake.wildcards.var
    config = deepcopy(snakemake.config)

   

    list_dsR = []
    for file in inputs:
        dsR = xr.open_zarr(file, decode_timedelta=False)
        list_dsR.append(dsR)

    ds= xr.concat(list_dsR, 'loc')

    #TODO: tmp just to make it work now
    ds.rlat.attrs['original_shape'] ='778x706'
    ds.rlon.attrs['original_shape'] ='778x706'
    ds.attrs['cat:domain'] = config['full_region']['name']


    ds = xs.clean_up(ds=ds,**config['clean_up']['xscen_clean_up'][var])
    # #TODO: check if it worked in yaml
    #ds.attrs['cat:domain'] = 'zarr'
    #ds.attrs['cat:_data_format_'] = 'zarr'

    # fix attrs 
                            
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


