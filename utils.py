import xarray as xr
import shutil

from xclim.sdba.measures import rmse
from xclim import atmos, sdba

from xscen.config import CONFIG, load_config
from xscen.io import save_to_zarr

def compute_properties(sim, ref, period):
    # TODO add more diagnostics, xclim.sdba and from Yannick (R2?)
    nan_count = sim.to_array().isnull().sum('time').mean('variable')
    hist = sim.sel(time=period)
    ref = ref.sel(time=period)

    # Je load deux des variables pour essayer d'éviter les KilledWorker et Timeout
    out = xr.Dataset(data_vars={
        'nan_count': nan_count,
        'tx_mean_rmse': rmse(atmos.tx_mean(hist.tasmax, freq='MS').chunk({'time': -1}),
                             atmos.tx_mean(ref.tasmax, freq='MS').chunk({'time': -1})),
        'tn_mean_rmse': rmse(atmos.tn_mean(tasmin=hist.tasmin, freq='MS').chunk({'time': -1}),
                             atmos.tn_mean(tasmin=ref.tasmin, freq='MS').chunk({'time': -1})),
         'prcptot_rmse': rmse(atmos.precip_accumulation(hist.pr, freq='MS').chunk({'time': -1}),
                              atmos.precip_accumulation(ref.pr, freq='MS').chunk({'time': -1})),

    })

    return out


def save_move_update(ds,pcat, init_path, final_path,info_dict=None, encoding=CONFIG['custom']['encoding'], mode=mode):
    save_to_zarr(ds, init_path, encoding=encoding, mode=mode)
    shutil.move(init_path,final_path, dirs_exist_ok=True)
    pcat.update_from_ds(ds=ds, path=final_path,info_dict=info_dict)