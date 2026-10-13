"""Search catalog, extract simulation on the right region and clean it up."""

from copy import deepcopy

import numpy as np
import xarray as xr
import xscen as xs

from workflow.scripts.utils import dask_cluster


if 1 == 0:  # trick vscode
    import snakemake

xr.set_options(
    netcdf_engine_order=[
        "h5netcdf",
        "netcdf4",
    ]
)


if __name__ == "__main__":
    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    pool = snakemake.wildcards.pool
    output = snakemake.output

    client = dask_cluster(snakemake.params, config["dask"]["client"])

    args = deepcopy(config["extraction"]["simulation"]["search_data_catalogs"])

    # get right sims from pool name
    poolsplit = pool.split("_")
    if "other_search_criteria" not in args:
        args["other_search_criteria"] = {}
    
    if poolsplit[0] == "ScenarioMIP":  # GCM
        args["other_search_criteria"].update({
            "source": poolsplit[1],
            "experiment": poolsplit[2],
        })
    else:  # RCM
        args["other_search_criteria"].update({
            "source": poolsplit[0],
            "experiment": poolsplit[2],
            "driving_model": poolsplit[1],
        })
    # search cat
    cat_sim_id = xs.search_data_catalogs(
        **args,
    )

    # extract all the member
    # FIXME: in a future version, capture tracking_ids here
    # https://github.com/Ouranosinc/ESPO-G/issues/15
    real = []
    for subcat in cat_sim_id.values():
        dict_sim = xs.extract_dataset(
            catalog=subcat,
            region=config["full_region"],
            **config["extraction"]["simulation"]["extract_dataset"],
        )
        ds_r = dict_sim["D"]
        ds_r = ds_r.expand_dims(realization=[ds_r.attrs["cat:id"]])
        real.append(ds_r)

    ds_sim = xr.concat(real, dim="realization")

    # nan weird individual timestep
    if "BCC-CSM2-MR" in pool:  # dtr around -30
        ds_sim["tasmin"] = ds_sim["tasmin"].where(
            ds_sim.time != (ds_sim.time.sel(time="2014-12-31").values),
        )
        ds_sim["dtr"] = ds_sim["dtr"].where(
            ds_sim.time != (ds_sim.time.sel(time="2014-12-31").values),
        )
    if "UKESM1-0-LL_ssp370" in pool:  # 1024mm on QC, replace with spatial neighbor mean
        latcorr = 49.375
        loncorr = 285.9375
        if (ds_sim['lat'].min() <= latcorr
            and ds_sim['lat'].max() >= latcorr
            and ds_sim['lon'].min() <= loncorr
            and ds_sim['lon'].max() >= loncorr
           ):
                
            ilat = ds_sim["lat"].values.tolist().index(latcorr)
            ilon = ds_sim["lon"].values.tolist().index(loncorr)
            mean_around = (
                ds_sim.sel(
                    time="2100-08-11",
                    realization="CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp370_r1i1p1f2_global",
                )
                .isel(
                    lat=slice(ilat - 1, ilat + 2),
                    lon=slice(ilon - 1, ilon + 2),
                )
                .squeeze()
                .pr.values
            )
            mean_around[1, 1] = np.nan
            fillval = np.nanmean(mean_around)
            ds_sim["pr"] = ds_sim["pr"].where(
                ~(
                    (ds_sim.lat == latcorr)
                    & (ds_sim.lon == loncorr)
                    & (ds_sim.time == ds_sim.time.sel(time="2100-08-11").values)
                    & (
                        ds_sim.realization
                        == "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp370_r1i1p1f2_global"
                    )
                ),
                other=fillval,
            )

    # https://errata.esgf.io/static/view.html?uid=76b3f818-d65f-c76b-bfd8-cae5bc27825c
    if "UKESM1-0-LL" in pool:
        ds_sim["tasmax"] = ds_sim["tasmax"].where(
            ds_sim.tasmax <= 335,
        )

    # clean up time
    ds_sim["time"] = ds_sim.time.dt.floor("D")

    if "mask" not in ds_sim and "create_mask" in config["extraction"]["simulation"]:
        ds_sim["mask"] = xs.regrid.create_mask(
            dict_sim["fx"], **config["extraction"]["simulation"]["create_mask"]
        )

    ds_sim = xs.clean_up(ds_sim, **config["extraction"]["clean_up"])

    # save to zarr
    xs.save_to_zarr(
        ds_sim,
        output["extract"],
        rechunk=config["chunks"]["pre-regrid"],
        **config["save_to_zarr"],
    )
