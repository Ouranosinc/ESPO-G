"""Concat all regions and clean up the dataset."""
import re
from copy import deepcopy

import geopandas as gpd
import xarray as xr
import xscen as xs


xr.set_options(keep_attrs=True)

if 1 == 0:  # trick vscode
    import snakemake


if __name__ == "__main__":
    # Get Snakemake parameters
    sim_id = snakemake.wildcards.sim_id
    inputs = snakemake.input.adjusted
    extracted = snakemake.input.extracted
    output = snakemake.output[0]
    var = snakemake.wildcards.var if 'var' in snakemake.wildcards.keys() else 'dtr'
    print(var)
    config = deepcopy(snakemake.config)

    list_dsr = []
    for file in inputs:
        dsr = xr.open_zarr(file, decode_timedelta=False)
        list_dsr.append(dsr)

    ds = xr.concat(list_dsr, "loc")

    # get the sim_id we want and finalize attrs and dims
    ds = ds.sel(realization=sim_id)
    ds = ds.drop("realization")
    if "ScenarioMIP" in sim_id:  # GCM
        ds.attrs["cat:member"] = re.search(r"r\d+i\d+p\d+f\d+", sim_id).group(0)
    else:  # RCM
        ds.attrs["cat:driving_member"] = re.search(r"r\d+i\d+p\d+f\d+", sim_id).group(0)
    ds.attrs["cat:id"] = xs.catalog.generate_id(ds).iloc[0]

    ds = xs.clean_up(ds=ds, **config["clean_up"]["xscen_clean_up"][var])

    # make sure we don't go outside the border of the inout data,
    # (extrapolation should only be for water inside the domain)
    ds_ext = xr.open_zarr(extracted, decode_timedelta=False)
    # TODO: until xscen PR 743 in the env
    if "crs" in ds_ext and "earth_radius" in ds_ext['crs'].attrs:
        ds_ext['crs'].attrs['earth_radius'] = float(ds_ext['crs'].attrs['earth_radius'])

    # only cut the original shape for RCM
    if "ScenarioMIP" not in sim_id:
        extent = xs.spatial.dataset_extent(ds_ext, method="shape")
        ds = xs.spatial.subset(
            ds, method="shape", shape=gpd.GeoDataFrame(geometry=[extent["shape"]])
        )

    chunks = xs.utils.translate_time_chunk(
        config["chunks"]["final"],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,
    )

    # coords lat, lon are not dask now, so will not be rechunked. need to do it by hand.
    if "rlat" in ds and "lat" in ds:
        ds["lat"] = ds["lat"].chunk({"rlat": chunks["Y"], "rlon": chunks["X"]})
        ds["lon"] = ds["lon"].chunk({"rlat": chunks["Y"], "rlon": chunks["X"]})

    xs.save_to_zarr(ds, output, **config["save_to_zarr"], rechunk=chunks)
