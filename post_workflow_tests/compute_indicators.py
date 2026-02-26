
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

    mod = xs.indicators.load_xclim_module('indicators')

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
                zip_zarrdir= "${SLURM_TMPDIR}",
                rechunk={"rlat":50, "rlon":50}
                )
    
    print('adjusted')
    for m in ['tasmin','DQM','Scaling']:
        for dm in ['MPI-ESM1-2-LR','CanESM5','NorESM2-MM']:
            print(glob.glob(f"{CONFIG[m]}/staging/simulation/biasadjusted/*_v20_CaSR/CMIP6/CORDEX/NAM/OURANOS/CRCM5-SN/{dm}/*/ssp370/r1/day/*/*.zarr.zip"))
            ds= xr.open_mfdataset(
                glob.glob(f"{CONFIG[m]}/staging/simulation/biasadjusted/*_v20_CaSR/CMIP6/CORDEX/NAM/OURANOS/CRCM5-SN/{dm}/*/ssp370/r1/day/*/*.zarr.zip"),
                engine='zarr')

            ds['tas']= xc.convert.mean_temperature_from_max_and_min(ds=ds)

            mod = xs.indicators.load_xclim_module('indicators')

            for name, ind in mod.iter_indicators():
                path=f"{CONFIG['pathind']}/{m}_{dm}_{name}.zarr.zip"
                if not Path(path).exists():
                    outd = xs.indicators.compute_indicators(ds, indicators=[(name,ind)])
                    out=outd['YS-JAN']
                    xs.save_to_zarr(
                        out,
                        path,
                        zip_zarrdir= "${SLURM_TMPDIR}",
                        rechunk={"rlat":50, "rlon":50}
                        )
    
    print('regridded')
    for dm in ['MPI-ESM1-2-LR','CanESM5','NorESM2-MM']:
        print(dm)
        d=[]
        for i in range(6):
            d.append(xr.open_zarr(glob.glob(f"{CONFIG['regDQM']}/CMIP6_CORDEX_{dm}_*sr-{i}+regridded.zarr")[0]))
        ds=xr.concat(d, dim='loc')
        ds=xs.utils.unstack_fill_nan(ds)

        ds['tas']= xc.convert.mean_temperature_from_max_and_min(ds=ds)

        mod = xs.indicators.load_xclim_module('indicators')

        for name, ind in mod.iter_indicators():
            path=f"{CONFIG['pathind']}/regridded_{dm}_{name}.zarr.zip"
            if not Path(path).exists():
                outd = xs.indicators.compute_indicators(ds, indicators=[(name,ind)])
                out=outd['YS-JAN']
                #out = out.chunk({ "rlat":50, "rlon":50})
                print(path)
                print(out)
                xs.save_to_zarr(
                    out,
                    path,
                    zip_zarrdir= "${SLURM_TMPDIR}",
                    rechunk={"time":-1,"rlat":50, "rlon":50}
                    )