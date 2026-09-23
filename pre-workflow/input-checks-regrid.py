"""Run health checks on inputs."""

from pathlib import Path

import numpy as np
import xclim as xc
import xscen as xs
import xarray as xr
from xscen import CONFIG
from copy import deepcopy


if __name__ == "__main__":

    xs.load_config(
        "../config/config_ESPO.yml",
        "../config/paths_ESPO.yml",
        reset=True,
    )
    ds_target = xr.open_zarr(
                    f"{CONFIG['paths']['final']}/reference/NAM_CaSR_stacked.zarr.zip",
                    decode_timedelta=False).compute()
    args=CONFIG["extraction"]["simulation"]["search_data_catalogs"].copy()
    # only check sim_ids that have issues in extract health checks
    args['other_search_criteria']['id']=[
        'CMIP6_CORDEX_CanESM5_r1i1p2f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12',
        'CMIP6_CORDEX_CanESM5_r1i1p2f1_OURANOS_CRCM5-SN_ssp585_r1_NAM-12',
        'CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp245_r5i1p1f1_global',
        'CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp370_r1i1p1f1_global',
        'CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp370_r5i1p1f1_global',
        'CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp585_r2i1p1f1_global',
        'CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp585_r5i1p1f1_global',
        'CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp585_r4i1p1f2_global',
    ]
    print(args)
    # search cat
    cat_sim_id = xs.search_data_catalogs(
        **args,
    )
    print(cat_sim_id.keys())
    for region_name in [ "NAM"]:
        region = CONFIG["full_region"] if region_name == "NAM" else CONFIG["QC"]
        if "tile_buffer" in region:
            del region["tile_buffer"]
        root_path = Path(f"{CONFIG['paths']['final']}/inputchecks/{region_name}")
        if not root_path.exists():
            root_path.mkdir(parents=True, exist_ok=True)

        for sim_id, dc_id in cat_sim_id.items():
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

                ds_input = ds.drop_vars("crs", errors="ignore")



                # Adjust intermediate grids
                if "intermediate_grids" in CONFIG["regrid"]["regrid_dataset"]:
                    intermediate_grids = deepcopy(
                        CONFIG["regrid"]["regrid_dataset"]["intermediate_grids"]
                    )
                    grids = deepcopy(intermediate_grids)
                    est_res = xs.spatial._estimate_grid_resolution(ds_input)
                    for key, grid_info in grids.items():
                        if (
                            grid_info["cf_grid_2d"]["d_lon"] > est_res[0]
                            or grid_info["cf_grid_2d"]["d_lat"] > est_res[1]
                        ):
                            # Delete intermediate grids that are too coarse
                            intermediate_grids.pop(key)
                            print(
                                f"Pop grid {key} with resolution {grid_info['cf_grid_2d']['d_lon']}x{grid_info['cf_grid_2d']['d_lat']} because it is coarser than the estimated input grid resolution {est_res[0]}x{est_res[1]}"
                            )

                    if len(intermediate_grids) > 0:
                        CONFIG["regrid"]["regrid_dataset"]["intermediate_grids"] = (
                            intermediate_grids
                        )
                    else:
                        CONFIG["regrid"]["regrid_dataset"].pop("intermediate_grids")

                ds_regrid = xs.regrid_dataset(
                    ds=ds_input, ds_grid=ds_target, **CONFIG["regrid"]["regrid_dataset"]
                )

                m= ds_regrid.pr.max().values
                print(m)
                print(m*86400)
                if m*86400>1650:
                    point=ds.where((ds.pr==m).compute(),drop=True)
                    print(point.lat.values,point.lon.values,point.time.values)


