import xarray as xr
import shutil
from pathlib import Path
import logging
import numpy as np

from xclim.sdba.measures import rmse
from xclim import atmos, sdba

from xscen.config import CONFIG, load_config
from xscen.io import save_to_zarr
from xscen.common import  maybe_unstack
logger = logging.getLogger('xscen')



load_config('paths_ESPO-G.yml', 'config_ESPO-G.yml', verbose=(__name__ == '__main__'), reset=True)
workdir = Path(CONFIG['paths']['workdir'])
exec_wdir = Path(CONFIG['paths']['exec_workdir'])
regriddir = Path(CONFIG['paths']['regriddir'])
workdir = Path(CONFIG['paths']['workdir'])
refdir = Path(CONFIG['paths']['refdir'])

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


def save_move_update(ds,pcat, init_path, final_path,info_dict=None,
                     encoding=CONFIG['custom']['encoding'], mode='o', itervar=False):
    save_to_zarr(ds, init_path, encoding=encoding, mode=mode,itervar=itervar)
    shutil.move(init_path,final_path)
    pcat.update_from_ds(ds=ds, path=str(final_path),info_dict=info_dict)


def calculate_properties(ds, pcat, step, unstack=False, diag_dict=CONFIG['diagnostics']['properties']):
    """
    Calculate diagnostic in the dictionary, save them all in one zarr and updates the catalog.
    The function verifies that a catalog entry doesn't exist already.
    The initial calculations are made in the workdir, but move to a permanent location afterwards.

    If the property is monthly or seasonal, we only keep the first month/season.

    :param ds: Input dataset (with tasmin, tasmax, pr) and the attrs we want to be passed to the final dataset
    :param pcat: Project Catalogue to update
    :param step: Type of input (ref, sim or scen)
    :param diag_dict: Dictionnary of properties to calculate. needs key func, var and args
    :return: A dataset with all properties
    """
    region_name = ds.attrs['cat/domain']
    if not pcat.exists_in_cat(domain=region_name, processing_level=f'diag_{step}', id=ds.attrs['cat/id']):
        for i, (name, prop) in enumerate(diag_dict.items()):
            logger.info(f"Calculating {step} diagnostic {name}")
            prop = eval(prop['func'])(da=ds[prop['var']], **prop['args']).load()

            if unstack:
                prop = maybe_unstack(
                    prop,
                    stack_drop_nans=CONFIG['custom']['stack_drop_nans'],
                    coords=refdir / f'coords_{region_name}.nc',
                    rechunk={d: CONFIG['custom']['out_chunks'][d] for d in ['lat', 'lon']}
                )
                prop=prop.transpose("lat", "lon")

            if "season" in prop.coords:
                prop = prop.isel(season=0)
                prop=prop.drop('season')
            if "month" in prop.coords:
                prop = prop.isel(month=0)
                prop=prop.drop('month')


            # put all properties in one dataset
            if i == 0:
                all_prop = prop.to_dataset(name=name)
            else:
                all_prop[name] = prop
        all_prop.attrs.update(ds.attrs)

        path_diag = Path(CONFIG['paths']['diagnostics'].format(region_name=region_name,
                                                               sim_id=ds.attrs['cat/id'],
                                                               step=step))
        path_diag_exec = f"{workdir}/{path_diag.name}"

        save_move_update(ds=all_prop, pcat=pcat, init_path=path_diag_exec, final_path=str(path_diag),
                         info_dict={'processing_level': f'diag_{step}'}, encoding=None)

        return all_prop



def save_diagnotics(ref, sim, scen, pcat):
    """
    calculate the biases amd the heat map and save
    Saves files of biases and heat map.
    :param ref: reference dataset
    :param sim: simulation dataset
    :param scen: scenario dataset
    :param pcat: project catalog to update
    """
    hmap = []
    #iterate through all available properties
    for i, var_name in enumerate(sim.data_vars):
        # get property
        prop_sim = sim[var_name]
        prop_ref = ref[var_name]
        prop_scen = scen[var_name]

        #calculate bias
        bias_scen_prop = sdba.measures.bias(sim=prop_scen, ref=prop_ref).load()
        bias_sim_prop = sdba.measures.bias(sim=prop_sim, ref=prop_ref).load()

        # put all bias in one dataset
        if i == 0:
            all_bias_scen_prop = bias_scen_prop.to_dataset(name=var_name)
            all_bias_sim_prop = bias_sim_prop.to_dataset(name=var_name)
        else:
            all_bias_scen_prop[var_name] = bias_scen_prop
            all_bias_sim_prop[var_name] = bias_sim_prop


        #mean the absolute value of the bias over all positions and add to heat map
        hmap.append([abs(bias_sim_prop).mean().values, abs(bias_scen_prop).mean().values])

    # plot heat map of biases ( 1 column per properties, 1 column for sim , 1 column for scen)
    hmap = np.array(hmap).T
    hmap = np.array(
        [(c - min(c)) / (max(c) - min(c)) if max(c) != min(c) else [0.5] * len(c) for c in
         hmap.T]).T

    path_diag = Path(CONFIG['paths']['diagnostics'].format(region_name=scen.attrs['cat/domain'],
                                                           sim_id=scen.attrs['cat/id'],
                                                           step='hmap'))
    #replace zarr by npy
    path_diag = path_diag.with_suffix('.npy')
    np.save(path_diag, hmap)

    all_bias_scen_prop.attrs.update(scen.attrs)
    all_bias_sim_prop.attrs.update(sim.attrs)
    for ds, step in zip([all_bias_scen_prop,all_bias_sim_prop],['scen_bias','sim_bias']):
        path_diag = Path(CONFIG['paths']['diagnostics'].format(region_name=scen.attrs['cat/domain'],
                                                               sim_id=scen.attrs['cat/id'],
                                                               step=step))
        save_to_zarr(ds=ds, filename=str(path_diag), mode='o')
        pcat.update_from_ds(ds=ds,
                            info_dict={'processing_level': f'diag_{step}'},
                            path=str(path_diag))

