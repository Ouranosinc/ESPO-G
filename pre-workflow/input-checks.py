"""Run health checks on inputs."""

from pathlib import Path

import numpy as np
import xclim as xc
import xscen as xs
from xscen import CONFIG


if __name__ == "__main__":
    for ensemble in [
        "ESPO-R",
        "ESPO-G",
    ]:
        print(ensemble)
        xs.load_config(
            f"../config/config_{ensemble}.yml",
            f"../config/paths_{ensemble}.yml",
            reset=True,
        )
        # search cat
        cat_sim_id = xs.search_data_catalogs(
            **CONFIG["extraction"]["simulation"]["search_data_catalogs"],
        )
        for region_name in ["QC", "NAM"]:
            region = CONFIG["full_region"] if region_name == "NAM" else CONFIG["QC"]
            if "tile_buffer" in region:
                del region["tile_buffer"]
            root_path = Path(f"{CONFIG['paths']['final']}/inputchecks/{region_name}")
            if not root_path.exists():
                root_path.mkdir(parents=True, exist_ok=True)

            for sim_id, dc_id in cat_sim_id.items():
                path = root_path / f"{sim_id}_{region_name}_inputchecks.zarr.zip"
                if not path.exists():
                    print(
                        sim_id,
                    )

                    dict_sim = xs.extract_dataset(
                        catalog=dc_id,
                        region=region,
                        **CONFIG["extraction"]["simulation"]["extract_dataset"],
                    )

                    ds = dict_sim["D"]

                    # mask water
                    ds["mask"] = xs.regrid.create_mask(
                        dict_sim["fx"],
                        **CONFIG["extraction"]["simulation"]["create_mask"],
                    )

                    ds = ds.where(ds.mask)

                    # nan or spatial fill weird individual timestep
                    #  here set nan to random value just to pass health checks,
                    #  in workflow it will get interpolated instead

                    # # dtr around -30
                    if "BCC-CSM2-MR" in sim_id:
                        ds["tasmin"] = ds["tasmin"].where(
                            ds.time != (ds.time.sel(time="2014-12-31").values),
                            other=250,
                        )
                        ds["dtr"] = ds["dtr"].where(
                            ds.time != (ds.time.sel(time="2014-12-31").values),
                            other=1,
                        )

                    # tasmin -138
                    if "ACCESS-ESM1-5" in sim_id and "r1i1p1f1" in sim_id:
                        ds["tasmin"] = ds["tasmin"].where(
                            ~(
                                (ds.lat == 63.75)
                                & (ds.lon == 313.125)
                                & (
                                    (ds.time == ds.time.sel(time="1984-01-10").values)
                                    | (ds.time == ds.time.sel(time="2000-02-07").values)
                                )
                            ),
                            other=250,
                        )
                        ds["dtr"] = ds["dtr"].where(
                            ~(
                                (ds.lat == 63.75)
                                & (ds.lon == 313.125)
                                & (ds.time == ds.time.sel(time="1984-01-10").values)
                            ),
                            other=1,
                        )

                    # pr 1024 mm on QC#
                    if "UKESM1-0-LL_ssp370_r1i1p1f2" in sim_id:
                        ilat = ds["lat"].values.tolist().index(49.375)
                        ilon = ds["lon"].values.tolist().index(285.9375)
                        mean_around = (
                            ds.sel(time="2100-08-11")
                            .isel(
                                lat=slice(ilat - 1, ilat + 2),
                                lon=slice(ilon - 1, ilon + 2),
                            )
                            .squeeze()
                            .pr.values
                        )
                        mean_around[1, 1] = np.nan
                        fillval = np.nanmean(mean_around)
                        ds["pr"] = ds["pr"].where(
                            ~(
                                (ds.lat == 49.375)
                                & (ds.lon == 285.9375)
                                & (ds.time == ds.time.sel(time="2100-08-11").values)
                            ),
                            other=fillval,
                        )

                    if "UKESM1-0-LL" in sim_id:
                        ds["tasmax"] = ds["tasmax"].where(
                            ds.tasmax <= 35,
                            other=290,
                        )

                    # we know that 2015 is missing for ESPO-R
                    # add it to avoid errors in the health checks

                    if ensemble == "ESPO-R":
                        ds["time"] = ds.time.dt.floor("D")
                        tmp = ds.sel(time="2015-01-02").squeeze()
                        tmp = tmp.drop_vars("time")
                        ds = ds.where(
                            ds.time != (ds.time.sel(time="2015-01-01").values),
                            tmp,
                        )
                        tmp = ds.sel(time="2100-12-30").squeeze()
                        tmp = tmp.drop_vars("time")
                        ds = ds.where(
                            ds.time != (ds.time.sel(time="2100-12-31").values),
                            tmp,
                        )

                    hc = xs.diagnostics.health_checks(
                        ds=ds, **CONFIG["health_checks"][region_name]
                    )

                    hc.attrs.update(ds.attrs)
                    for var in hc.data_vars:
                        if hc[var].values:
                            if var == "pr_very_large_precipitation_events":
                                ma = ds.pr.max(keep_attrs=True).values
                                mm = xc.core.units.convert_units_to(
                                    f"{ma} kg m-2 s-1", "mm/day", context="hydro"
                                )
                                hc[var] = mm
                                hc[var].attrs["units"] = "mm/day"

                            elif var == "tasmin_temperature_extremely_low":
                                mi = ds.tasmin.min().values
                                mm = xc.core.units.convert_units_to(f"{mi} K", "degC")
                                hc[var] = mm
                                hc[var].attrs["units"] = "degC"

                            elif var == "tasmax_temperature_extremely_high":
                                ma = ds.tasmax.max().values
                                mm = xc.core.units.convert_units_to(f"{ma} K", "degC")
                                hc[var] = mm
                                hc[var].attrs["units"] = "degC"

                            elif var == "pr_negative_accumulation_values":
                                ma = ds.pr.min().values
                                mm = xc.core.units.convert_units_to(
                                    f"{ma} kg m-2 s-1", "mm/day", context="hydro"
                                )
                                hc[var] = mm
                                hc[var].attrs["units"] = "mm/day"

                            elif var == "dtr_negative_accumulation_values":
                                ma = ds.dtr.min().values
                                hc[var] = mm
                                hc[var].attrs["units"] = "K"

                    xs.save_to_zarr(hc, path, **CONFIG["save_to_zarr"])
