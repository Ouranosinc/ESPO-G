from copy import deepcopy
import xscen as xs
import xclim as xc
import xarray as xr
import numpy as np
from datetime import datetime
xr.set_options(keep_attrs=True)
from workflow.scripts.utils import dask_cluster
from xscen.xclim_modules import conversions
from pathlib import Path
import geopandas as gpd
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    inputs=snakemake.input.adjusted
    extracted=snakemake.input.extracted
    output=snakemake.output[0]
    var=snakemake.wildcards.var
    config = deepcopy(snakemake.config)

    list_dsR = []
    for file in inputs:
        dsR = xr.open_zarr(file, decode_timedelta=False)
        list_dsR.append(dsR)

    ds= xr.concat(list_dsR, 'loc')

    ds = xs.clean_up(ds=ds,**config['clean_up']['xscen_clean_up'][var])

    # make sure we don't go outside the border of the inout data, 
    # (extrapolation should only be for water inside the domain)
    ds_ext= xr.open_zarr(extracted, decode_timedelta=False)
    extent = xs.spatial.dataset_extent(ds_ext, method='shape')
    ds=xs.spatial.subset(ds, method='shape', 
                            shape=gpd.GeoDataFrame(geometry=[extent['shape']]))


    chunks=xs.utils.translate_time_chunk(
        config['chunks']['final'],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,)
    
    # coords lat, lon are not dask now, so will not be rechunked. need to do it by hand.
    if 'rlat' in ds and 'lat' in ds:
        ds['lat']=ds['lat'].chunk({'rlat' :chunks['Y'], 'rlon': chunks['X']})  
        ds['lon']=ds['lon'].chunk({'rlat' :chunks['Y'], 'rlon': chunks['X']})
    
    xs.save_to_zarr(
        ds, 
        output, 
        **config['save_to_zarr'],
        rechunk=chunks
        )


