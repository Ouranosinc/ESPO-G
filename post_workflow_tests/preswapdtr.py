"""Check what happens if we use dtr instead of swapping"""

import glob
import re
from pathlib import Path

import xarray as xr
import xscen as xs
from xscen import CONFIG


if __name__ == "__main__":
    ensemble = "ESPO-R"
    xs.load_config(
        f"../config/config_{ensemble}.yml",
        f"../config/paths_{ensemble}.yml",
        reset=True,
    )
    for f in glob.glob(f"{CONFIG['paths']['final']}/preswap/*CRCM5*"):
        print(f)
        ds = xr.open_zarr(f)

        source = ds.attrs["cat:source"]
        driving_model = ds.attrs["cat:driving_model"]
        experiment = ds.attrs["cat:experiment"]
        member = re.search(r"r\d+i\d+p\d+f\d+", f).group(0)
        print(member)
        final_path = f"{CONFIG['paths']['final']}/preswap/testdiff"
        if not Path(final_path).exists():
            Path(final_path).mkdir(parents=True, exist_ok=True)

        if not Path(
            f"{final_path}/diff_tasmin_{source}_{experiment}_{member}.zarr.zip"
        ).exists():
            mask = ds.dtr >= 0
            path = f"{CONFIG['paths']['final']}/staging/simulation/biasadjusted/ESPO_v20_CaSR/CMIP6/CORDEX/NAM/OURANOS/CRCM5-SN/{driving_model}/{member}/{experiment}/*/day/"
            print(path)
            ds_tasmin_old = xr.open_zarr(
                glob.glob(f"{path}/tasmin/*")[0], decode_timedelta=False
            )
            ds_tasmax_old = xr.open_zarr(
                glob.glob(f"{path}/tasmax/*")[0], decode_timedelta=False
            )
            ds_dtr_old = xr.open_zarr(
                glob.glob(f"{path}/dtr/*")[0], decode_timedelta=False
            )

            ds_tasmax_new = ds_tasmax_old.copy()
            ds_tasmin_new = ds_tasmin_old.copy()

            ds_tasmax_new["tasmax"] = ds_tasmax_old["tasmax"].where(
                mask, other=ds_tasmin_old.tasmin
            )
            ds_tasmin_new["tasmin"] = ds_tasmin_old["tasmin"].where(
                mask, other=ds_tasmin_old.tasmin - ds_dtr_old.dtr
            )

            diff_tasmax = ds_tasmax_new - ds_tasmax_old
            diff_tasmax = diff_tasmax.where(~mask)

            diff_tasmin = ds_tasmin_new - ds_tasmin_old
            diff_tasmin = diff_tasmin.where(~mask)

            xs.save_to_zarr(
                ds_tasmax_new,
                f"{final_path}/tasmax_{driving_model}_{source}_{experiment}_{member}.zarr.zip",
                zip_zarrdir="${SLURM_TMPDIR}",
            )
            xs.save_to_zarr(
                ds_tasmin_new,
                f"{final_path}/tasmin_{driving_model}_{source}_{experiment}_{member}.zarr.zip",
                zip_zarrdir="${SLURM_TMPDIR}",
            )
            xs.save_to_zarr(
                diff_tasmax,
                f"{final_path}/diff_tasmax_{driving_model}_{source}_{experiment}_{member}.zarr.zip",
                zip_zarrdir="${SLURM_TMPDIR}",
            )
            xs.save_to_zarr(
                diff_tasmin,
                f"{final_path}/diff_tasmin_{driving_model}_{source}_{experiment}_{member}.zarr.zip",
                zip_zarrdir="${SLURM_TMPDIR}",
            )
