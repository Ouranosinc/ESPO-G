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

    ds = xs.clean_up(ds=ds,**config['clean_up']['xscen_clean_up'][var])



    # FIXME: use xscen when >0.14
    import shapely as shp
    # def dataset_extent(ds: xr.Dataset, method: str = "shape", name: str | None = None) :
    #     from xscen.regrid import create_bounds_gridmapping

    #     if "lat_bounds" not in ds:
    #         if "lat" in ds and ds.lat.ndim == 1:
    #             ds = ds.cf.add_bounds(["lon", "lat"])
    #         else:
    #             ds = create_bounds_gridmapping(ds, gridmap='crs') #crs added by JL
    #     if ds["lat_bounds"].ndim == 2:
    #         lonb = ds.lon_bounds.isel(bounds=xr.DataArray([0, 0, 1, 1], dims=("bounds",)))
    #         latb = ds.lat_bounds.isel(bounds=xr.DataArray([0, 1, 1, 0], dims=("bounds",)))
    #         lonb, latb = xr.broadcast(lonb, latb)
    #     else:
    #         lonb, latb = ds.lon_bounds, ds.lat_bounds

    #     region = {"method": method}
    #     if name is not None:
    #         region["name"] = name

    #     # Tolerance 0 is to merge colinear segments, without degrading anything else
    #     p = shp.simplify(
    #         shp.unary_union(shp.polygons(shp.linearrings(lonb.transpose(..., "bounds"), latb.transpose(..., "bounds")))),
    #         tolerance=0,
    #     )

    #     match method:
    #         case "shape":
    #             region["shape"] = p
    #         case "bbox":
    #             bnds = p.bounds
    #             region["lon_bnds"] = [bnds[0], bnds[2]]
    #             region["lat_bnds"] = [bnds[1], bnds[3]]
    #         case _ as err:
    #             raise ValueError(f"Method must be 'shape' or 'bbox'. Got {err}.")

    #     return region


    # make sure we don't go outside the border of the inout data, 
    # (extrapolation should only be for water inside the domain)
    extent = xs.spatial.dataset_extent(ds, method='shape')
    ds=xs.spatial.subset(ds, method='shape', name='original input extent',
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


