
import xscen as xs
import xarray as xr
from xscen import CONFIG
import xclim as xc
import datetime
from dask.distributed import Client
import os
import sys
import time
import glob
from pathlib import Path

xs.load_config( "paths_post-workflow.yml")


if __name__ == '__main__':
    print('reference')
    ds = xr.open_zarr(f"{CONFIG['DQM']}/reference/NAM_CaSR_default.zarr.zip")
    ds['tas']= xc.convert.mean_temperature_from_max_and_min(ds=ds)
    ds=ds.chunk({"time": -1, "rlat":50, "rlon":50})

    mod = xs.indicators.load_xclim_module('indicators.yml')

    for name, ind in mod.iter_indicators():
        path=f"{CONFIG['pathind']}/CaSR_{name}.zarr.zip"
        if not Path(path).exists():
            outd = xs.indicators.compute_indicators(ds, indicators=[(name,ind)])
            out=outd['YS-JAN']

            for v in out.coords:
                if 'chunks' in out[v].encoding:
                    del out[v].encoding['chunks']

            xs.save_to_zarr(
                out,
                path,
                zip_zarrdir= "${SLURM_TMPDIR}"
                )

    for m in ['tasmin','DQM','Scaling']:
        for dm in ['MPI-ESM1-2-LR','CanESM5','NorESM2-MM']:
            print(glob.glob(f"{CONFIG[m]}/staging/simulation/biasadjusted/*_v20_CaSR/CMIP6/CORDEX/NAM/OURANOS/CRCM5-SN/{dm}/*/ssp370/r1/day/*/*.zarr.zip"))
            ds= xr.open_mfdataset(
                glob.glob(f"{CONFIG[m]}/staging/simulation/biasadjusted/*_v20_CaSR/CMIP6/CORDEX/NAM/OURANOS/CRCM5-SN/{dm}/*/ssp370/r1/day/*/*.zarr.zip"),
                engine='zarr')

            ds['tas']= xc.convert.mean_temperature_from_max_and_min(ds=ds)

            mod = xs.indicators.load_xclim_module('indicators.yml')

            for name, ind in mod.iter_indicators():
                path=f"{CONFIG['pathind']}/{m}_{dm}_{name}.zarr.zip"
                if not Path(path).exists():
                    outd = xs.indicators.compute_indicators(ds, indicators=[(name,ind)])
                    out=outd['YS-JAN']
                    xs.save_to_zarr(
                        out,
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}"
                        )