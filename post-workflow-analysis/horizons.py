"""Compute climatological means of indicators."""

import os
from pathlib import Path

import xclim as xc
import xscen as xs
from xscen import CONFIG


xs.load_config(
    "../config/ARCHES/config_ARCHES.yml",
    "../config/ARCHES/paths_ARCHES.yml",
    reset=True,
)
cat = xs.ProjectCatalog(f"{CONFIG['arches']}/cat_ARCHES.json")
if not Path(f"{CONFIG['arches']}/ensembles/horizons").exists():
    Path(f"{CONFIG['arches']}/ensembles/horizons").mkdir(parents=True, exist_ok=True)

# FIXME: until xscen> 0.15.2 give IPCC file
tas_src = f"{CONFIG['paths']['home']}/post-workflow-analysis/IPCC_annual_global_tas.nc"


if __name__ == "__main__":
    cat_sim = xs.search_data_catalogs(
        data_catalogs=[cat],
        variables_and_freqs={"tasmin": "D", "tasmax": "D", "pr": "D"},
        restrict_warming_level={
            "wl": [2],
            "window": 30,
            "ignore_member": True,
            "tas_src": tas_src,
        },
        other_search_criteria={"bias_adjust_project": "ESPO"},
    )
    timeseries_dict = {}
    for sim_id, dc in cat_sim.items():
        path = f"{CONFIG['arches']}/ensembles/horizons/{sim_id}_horizons.zarr.zip"
        if not os.path.exists(path):
            print(sim_id)
            ds_input = xs.extract_dataset(
                catalog=dc,
                region=CONFIG["diagregion"]["Atlas"],
                xr_open_kwargs={"drop_variables": ["mask", "orog"]},
            )["D"]

            ds_hor = xs.produce_horizon(
                ds_input,
                indicators=f"{CONFIG['paths']['home']}/post-workflow-analysis/indicators.yml",
                periods=["1991", "2020"],
                warminglevels={
                    "wl": [2],
                    "window": 30,
                    "ignore_member": True,
                    "tas_src": tas_src,
                },
            )

            ds_hor["prcptot"] = xc.core.units.convert_units_to(
                ds_hor["prcptot"], "mm", context="hydro"
            )
            ds_hor["tx_mean"] = xc.core.units.convert_units_to(
                ds_hor["tx_mean"], "degC"
            )
            ds_hor["tn_mean"] = xc.core.units.convert_units_to(
                ds_hor["tn_mean"], "degC"
            )
            ds_hor = ds_hor.chunk({"rlat": 50, "rlon": 50})
            for v in ["lat", "lon"]:
                if "chunks" in ds_hor[v].encoding:
                    del ds_hor[v].encoding["chunks"]

            xs.save_to_zarr(ds_hor, path, zip_zarrdir="${SLURM_TMPDIR}")
