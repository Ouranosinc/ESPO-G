"""Create tasmax and tasmin for method DQM-dtr."""

import datetime
from pathlib import Path

import xarray as xr
import xscen as xs
from xscen import CONFIG


xs.load_config(
    "../config/ARCHES/config_ARCHES.yml",
    "../config/ARCHES/paths_ARCHES.yml",
    reset=True,
)
cat = xs.ProjectCatalog(f"{CONFIG['arches']}/cat_ARCHES.json")


if __name__ == "__main__":
    # s=sys.argv[1]
    # print(s)
    for sim_id, ds in (
        cat.search(bias_adjust_project="ESPO", experiment="ssp370")
        .to_dataset_dict()
        .items()
    ):
        oldpath = cat.search(
            id=sim_id.replace(".NAM.biasadjusted.D", ""), variable="tasmax"
        ).df.path.iloc[0]
        print(oldpath)
        newpath = (
            oldpath.replace(CONFIG["espo"], CONFIG["dqm-dtr"])
            .replace("ESPO6", "DQM-dtr")
            .replace("ESPO", "DQM-dtr")
        )
        print(newpath)
        if not Path(newpath.replace("tasmax", "tasmin")).exists():
            sim_id = sim_id.replace(".NAM.biasadjusted.D", "").replace(
                "ESPO_CaSR_", "ESPO6_v20_CaSR+"
            )
            if "ScenarioMIP" in sim_id:
                sim_id = sim_id.replace("_NAM", "_global_NAM")
            else:
                sim_id = sim_id.replace("_NAM", "_NAM-12_NAM")
            # original dtr to find mask of inversions.
            dtrpreswap = xr.open_zarr(
                f"{CONFIG['espo']}/preswap/dtrpreswap_day_{sim_id}.zarr.zip"
            )
            valid_mask = dtrpreswap > 0
            # get back original tasmax (not swapped)
            swaptasmax = ds["tasmax"].copy()
            swaptasmin = ds["tasmin"].copy()
            unswaptasmax = ds["tasmax"].where(
                valid_mask.dtr.compute(), other=swaptasmin
            )

            # compute tasmin from adjusted dtr and adjusted unswap tasmax

            tasmin = unswaptasmax - ds["dtr"]

            unswaptasmax = unswaptasmax.to_dataset(name="tasmax")
            unswaptasmax["tasmax"].attrs["history"] = (
                f"[{datetime.now():%Y-%m-%d %H:%M:%S}] unswap tasmax based on preswapdtr.\n"
            ) + unswaptasmax["tasmax"].attrs["history"]

            tasmin = tasmin.to_dataset(name="tasmin")
            tasmin["tasmin"].attrs["history"] = (
                f"[{datetime.now():%Y-%m-%d %H:%M:%S}] tasmin computed from adjusted dtr and \
                adjusted tasmax before the swap.\n"
            )
            if not Path(newpath).exists():
                Path(newpath).parent.mkdir(parents=True, exist_ok=True)
                xs.save_to_zarr(
                    unswaptasmax,
                    newpath,
                    zip_zarrdir="${SLURM_TMPDIR}",
                )
            if not Path(newpath.replace("tasmax", "tasmin")).exists():
                Path(newpath.replace("tasmax", "tasmin")).parent.mkdir(
                    parents=True, exist_ok=True
                )
                xs.save_to_zarr(
                    tasmin,
                    newpath.replace("tasmax", "tasmin"),
                    zip_zarrdir="${SLURM_TMPDIR}",
                )
