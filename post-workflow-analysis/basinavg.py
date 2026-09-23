"""Compute the average of the precipitation over the basins."""

import glob
from pathlib import Path

import geopandas as gpd
import pandas as pd
import xarray as xr
import xclim as xc
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

if not Path(f"{CONFIG['arches']}/bilan_pr").exists():
    Path(f"{CONFIG['arches']}/bilan_pr").mkdir(parents=True, exist_ok=True)


def compute_ind_on_basin_avg(ds, gdfs, j):
    """
    Compute the average of the precipitation over the basins.
    Then, compute prcptot, rx1day and rx5day on the basin average.
    """
    cur = xs.spatial_mean(
        ds,
        method="xesmf",
        region=dict(name="tmp", method="shape", shape=gdfs.iloc[[j]]),
        simplify_tolerance=tol,
        kwargs={"skipna": True},
    )
    cur = cur.sel(time=slice("1991", "2020"))
    cur = cur.chunk({"time": -1})

    out = xc.atmos.max_n_day_precipitation_amount(
        ds=cur, window=5, freq="MS"
    ).to_dataset()

    out["rx1day"] = xc.atmos.max_n_day_precipitation_amount(ds=cur, window=1, freq="MS")

    out["prcptot"] = xc.atmos.precip_accumulation(ds=cur, freq="MS")

    df_cur = out.to_dataframe().reset_index()
    df_cur["basin_id"] = j
    #df_cur['month'] = pd.to_datetime(df_cur['time']).dt.strftime('%b').str.upper()
    #df_cur['monthnum'] = pd.to_datetime(df_cur['time']).dt.month
    return df_cur


if __name__ == "__main__":
    lgdfs = []
    files = glob.glob(f"{CONFIG['data']}/region_shapefiles/*.shp")
    for f in files:
        lgdfs.append(gpd.read_file(f))
    gdfsa = pd.concat(lgdfs)

    bbox = box(-83, 42, -55, 53)
    gdfs6 = gpd.read_file(f"{CONFIG['data']}/hydrobasins/hybas_na_lev06_v1c.shp")
    gdfs6 = gdfs6[gdfs6.geometry.within(bbox)]  # in atlas region
    gdfs6 = gdfs6[gdfs6["SUB_AREA"] > 200]  # bigger than one grid point
    tol = 0.01

    ds_ref = xr.open_zarr(f"{CONFIG['espo']}/reference/NAM_CaSR_fullregion.zarr.zip")
    ds_ref = ds_ref.chunk({"time": -1, "rlat": 50, "rlon": 50})

    for gdfs, geoname in zip([gdfsa, gdfs6], ["atlas", "lev06"], strict=True):
        print(geoname)
        path = Path(f"{CONFIG['arches']}/bilan_pr/bassinavg_{geoname}_CaSR.csv")
        if not path.exists():
            l_ref = []
            for j in range(len(gdfs)):
                print(j)
                l_ref.append(compute_ind_on_basin_avg(ds_ref, gdfs, j))
            df_ref = pd.concat(l_ref, ignore_index=True)
            df_ref.to_csv(path)

    sim_dict = cat.search(
        bias_adjust_project="ESPO",
        variable="pr",
        experiment="ssp370",
        source=[   'CRCM5-SN'
                 ],
    ).to_dataset_dict()
    #'CRCM5-SN',
    # 'NorESM2-LM', 'NorESM2-MM', 'MRI-ESM2-0', 'GFDL-ESM4',
    # 'INM-CM4-8', 'INM-CM5-0','MPI-ESM1-2-HR', 'EC-Earth3',
    # 'EC-Earth3-Veg', 'CanESM5-1', 'CanESM5', 'FGOALS-g3',
    # 'BCC-CSM2-MR', 'IPSL-CM6A-LR', 'MIROC-ES2L', 'MIROC6',
    # 'TaiESM1', 'CNRM-CM6-1', 'CNRM-ESM2-1', 'CMCC-ESM2',
    #  'ACCESS-ESM1-5', 'UKESM1-0-LL', 'ACCESS-CM2', 'MPI-ESM1-2-LR',
    for sim_id, ds_adj in sim_dict.items():
        sim_id = sim_id.replace(".NAM.biasadjusted.D", "")
        print(sim_id)
        for gdfs, geoname in zip([gdfsa, gdfs6], ["atlas", "lev06"], strict=True):
            print(geoname)
            path = Path(f"{CONFIG['arches']}/bilan_pr/bassinavg_{geoname}_{sim_id}.csv")
            if not path.exists():
                l_adj = []
                for j in range(len(gdfs)):
                    print(j)
                    l_adj.append(compute_ind_on_basin_avg(ds_adj, gdfs, j))
                df_adj = pd.concat(l_adj, ignore_index=True)
                df_adj.to_csv(path)
