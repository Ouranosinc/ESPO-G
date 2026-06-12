"""Run health checks on inputs."""

from pathlib import Path

import xclim as xc
import xscen as xs
from xscen import CONFIG


if __name__ == "__main__":
    for ensemble in [
        #"ESPO-G", 
        "ESPO-R"
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
        root_path = Path(f"{CONFIG['paths']['final']}/inputcheckslarge/")
        if not root_path.exists():
            root_path.mkdir(parents=True, exist_ok=True)

        for sim_id, dc_id in cat_sim_id.items():
            path = root_path / f"{sim_id}_inputchecks.zarr.zip"
            if not path.exists():
                print(
                    sim_id,
                )

                ds = xs.extract_dataset(
                    catalog=dc_id,
                    region=CONFIG["full_region"],
                    **CONFIG["extraction"]["simulation"]["extract_dataset"],
                )["D"]

                # we know that 2015 is missing for ESPO-R
                # add it to avoid errors in the health checks
                if ensemble == "ESPO-R":
                    ds.loc[dict(time="2015-01-01")] = 270

                hc = xs.diagnostics.health_checks(
                    ds=ds, **CONFIG["health_checks"]["extract"]
                )

                hc.attrs.update(ds.attrs)
                for var in hc.data_vars:
                    if hc[var].values:
                        if var == "pr_very_large_precipitation_events":
                            ma = ds.pr.max(keep_attrs=True).values
                            mm = xc.core.units.convert_units_to(
                                f"{ma} kg m-2 s-1", "mm/day", context="hydro"
                            )
                            print(mm)
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
