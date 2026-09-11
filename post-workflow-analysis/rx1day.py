"""Compute the rx1day for different grids."""

import glob
from copy import deepcopy
from pathlib import Path

import geopandas as gpd
import pandas as pd
import xarray as xr
import xclim as xc
import xesmf
import xscen as xs
from shapely.geometry import box
from xscen import CONFIG


xs.load_config(
    "../config/ARCHES/config_ARCHES.yml",
    "../config/ARCHES/paths_ARCHES.yml",
    reset=True,
)
cat = xs.ProjectCatalog(f"{CONFIG['arches']}/cat_ARCHES.json")
cat_sim = xs.DataCatalog(
    CONFIG["extraction"]["simulation"]["search_data_catalogs"]["data_catalogs"][0]
)


Path(f"{CONFIG['arches']}/rx1day/espo").mkdir(parents=True, exist_ok=True)
Path(f"{CONFIG['arches']}/prcptot/espo").mkdir(parents=True, exist_ok=True)
Path(f"{CONFIG['arches']}/rx1day/reg1km").mkdir(parents=True, exist_ok=True)
Path(f"{CONFIG['arches']}/rx1day/reg10km").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    # sim_dict = xs.search_data_catalogs(
    #     data_catalogs=cat,
    #     variables_and_freqs={"pr": "D"},
    #     #restrict_members={"ordered": 1},
    #     other_search_criteria=dict(
    #         bias_adjust_project="ESPO",
    #         experiment="ssp370",
    #     ),
    # )
    sim_dict = cat.search(
        bias_adjust_project="ESPO", experiment="ssp370", variable="pr"
    ).to_dataset_dict()

    for sim_id, ds_adj in sim_dict.items():
        sim_id = sim_id.replace(".NAM.biasadjusted.D", "")

        print(sim_id)
        sim_id_raw = sim_id.replace("ESPO_CaSR_", "")
        if "ScenarioMIP" in sim_id:
            sim_id_raw = sim_id_raw.replace("_NAM", "_global")
        else:
            sim_id_raw = sim_id_raw.replace("_NAM", "_NAM-12")
        print(sim_id_raw)

        # get raw data
        # args = deepcopy(CONFIG["extraction"]["simulation"]["search_data_catalogs"])
        # args["other_search_criteria"] = {"id": sim_id_raw}
        # # search cat
        # cat_sim_id = xs.search_data_catalogs(
        #     **args,
        # )
        # ds_raw = xs.extract_dataset(
        #     catalog=next(iter(cat_sim_id.values())),
        #     region=CONFIG["full_region"],
        #     **CONFIG["extraction"]["simulation"]["extract_dataset"],
        # )["D"]

        path = Path(f"{CONFIG['arches']}/rx1day/espo/rx1day_{sim_id}_espo.zarr.zip")
        if not path.exists():
            ds_adj = xs.spatial.subset(ds_adj, **CONFIG["QC"])
            out = xc.atmos.max_1day_precipitation_amount(ds_adj.pr).to_dataset()
            out.attrs = ds_adj.attrs
            out = out.chunk({"time": -1, "rlat": 10, "rlon": 10})
            # remove chunk encoding of coords
            for coords in out.coords:
                if "chunks" in out[coords].encoding:
                    del out[coords].encoding["chunks"]

            xs.save_to_zarr(
                out,
                path,
                zip_zarrdir="${SLURM_TMPDIR}",
            )

        # sneak in a prcptot for espo
        path = Path(f"{CONFIG['arches']}/prcptot/espo/prcptot_{sim_id}_espo.zarr.zip")
        if not path.exists():
            ds_adj = xs.spatial.subset(ds_adj, **CONFIG["QC"])
            out = xc.atmos.precip_accumulation(ds_adj.pr).to_dataset()
            out.attrs = ds_adj.attrs
            out = out.chunk({"time": -1, "rlat": 10, "rlon": 10})
            # remove chunk encoding of coords
            for coords in out.coords:
                if "chunks" in out[coords].encoding:
                    del out[coords].encoding["chunks"]

            xs.save_to_zarr(
                out,
                path,
                zip_zarrdir="${SLURM_TMPDIR}",
            )

        # path = Path(f"{CONFIG['arches']}/rx1day/reg1deg/rx1day_{sim_id}_reg1deg.zarr.zip")
        # if not path.exists():
        #     ds_grid = xesmf.util.cf_grid_2d(
        #         lon0_b=179.05, lon1_b=351.2, d_lon=1, lat0_b=9, lat1_b=84, d_lat=1
        #     )
        #     ds_grid = xs.spatial.subset(ds_grid, **CONFIG["QC"])
        #     ds_reg = xs.regrid_dataset(
        #         ds_raw,
        #         ds_grid,
        #         regridder_kwargs={
        #             "method": "bilinear",
        #             "extrap_method": "inverse_dist",
        #         },
        #     )

        #     out = xc.atmos.max_1day_precipitation_amount(ds_reg.pr).to_dataset()
        #     out.attrs = ds_reg.attrs
        #     out = out.chunk({"time": -1, "lat": 10, "lon": 10})
        #     # remove chunk encoding of coords
        #     for coords in out.coords:
        #         if "chunks" in out[coords].encoding:
        #             del out[coords].encoding["chunks"]

        #     xs.save_to_zarr(
        #         out,
        #         path,
        #         zip_zarrdir="${SLURM_TMPDIR}",
        #     )

        # path = Path(
        #     f"{CONFIG['arches']}/rx1day/reg10km/rx1day_{sim_id}_reg10km.zarr.zip"
        # )
        # if not path.exists():
        #     ds_grid = xr.open_zarr(
        #         f"{CONFIG['paths']['final']}/reference/NAM_CaSR_fullregion.zarr.zip"
        #     )
        #     ds_grid = xs.spatial.subset(ds_grid, **CONFIG["QC"])
        #     args = deepcopy(CONFIG["regrid"]["regrid_dataset"])
        #     args["regridder_kwargs"] = {
        #         "method": "bilinear",
        #         "extrap_method": "inverse_dist",
        #         "locstream_out": False,
        #         "reuse_weights": False,
        #     }
        #     ds_reg = xs.regrid_dataset(ds_raw, ds_grid, **args)

        #     out = xc.atmos.max_1day_precipitation_amount(ds_reg.pr).to_dataset()
        #     out.attrs = ds_reg.attrs
        #     out = out.chunk({"time": -1, "rlat": 10, "rlon": 10})
        #     # remove chunk encoding of coords
        #     for coords in out.coords:
        #         if "chunks" in out[coords].encoding:
        #             del out[coords].encoding["chunks"]

        #     xs.save_to_zarr(
        #         out,
        #         path,
        #         zip_zarrdir="${SLURM_TMPDIR}",
        #     )
