
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
from datetime import datetime
import numpy as np
import xsdba
from copy import deepcopy
import sys

xs.load_config("../config/ARCHES/config_Scaling.yml",  "../config/ARCHES/paths_Scaling.yml", reset=True)
cat = xs.ProjectCatalog(f'{CONFIG['paths']['final']}/cat_ARCHES.json')


if __name__ == '__main__':
    if not Path(f"{CONFIG['arches']}/inversion").exists():
        Path(f"{CONFIG['arches']}/inversion").mkdir(parents=True, exist_ok=True)

    swaps=[]
    totals=[]
    for sim_id, ds in cat.search(bias_adjust_project='ESPO', experiment='ssp370').to_dataset_dict().items():
            sim_id=sim_id.replace('.NAM.biasadjusted.D','').replace('ESPO_CaSR_','ESPO6_v20_CaSR+')
            if 'ScenarioMIP' in sim_id:
                sim_id=sim_id.replace('_NAM','_global_NAM')
            else:
                sim_id=sim_id.replace('_NAM','_NAM-12_NAM')
            # original dtr to find mask of inversions.
            dtrpreswap=xr.open_zarr(f"{CONFIG['espo']}/preswap/dtrpreswap_day_{sim_id}.zarr.zip")
            dtrpreswap=dtrpreswap.convert_calendar(calendar='standard', use_cftime=False, align_on='year')
            swap= (dtrpreswap<0).resample(time='QS-DEC').sum()
            swap=swap.sel(time=slice('1951-01','2099-11'))
            swap=xs.utils.unstack_dates(swap).expand_dims(realization=[sim_id])
            total= dtrpreswap.resample(time='QS-DEC').count()
            total=total.sel(time=slice('1951-01','2099-11'))
            total=xs.utils.unstack_dates(total).expand_dims(realization=[sim_id])

        
            swaps.append(swap)
            totals.append(total)
    #swaps=[ds.convert_calendar(calendar='standard', use_cftime=True, align_on='year') for ds in swaps]
    #totals=[ds.convert_calendar(calendar='standard', use_cftime=True, align_on='year') for ds in totals]

    ds_swap=xr.concat(swaps, dim='realization')
    ds_total=xr.concat(totals, dim='realization')
    print(ds_swap)
    print(ds_swap.time)

    p=f"{CONFIG['arches']}/inversion/ds_swap.zarr.zip"
    if not Path(p).exists():
        xs.save_to_zarr(ds_swap, p,zip_zarrdir= "${SLURM_TMPDIR}",)
    p=f"{CONFIG['arches']}/inversion/ds_total.zarr.zip"
    if not Path(p).exists():
        xs.save_to_zarr(ds_total, p,zip_zarrdir= "${SLURM_TMPDIR}",)