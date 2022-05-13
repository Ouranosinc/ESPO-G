from dask.distributed import Client
from dask import config as dskconf
import atexit
from pathlib import Path
import xarray as xr
import shutil
import numpy as np
import json
import logging
from matplotlib import pyplot as plt
import os
from dask.diagnostics import ProgressBar
import pandas as pd

from xclim import atmos
from xclim.core.calendar import convert_calendar, get_calendar, date_range_like
from xclim.core.units import convert_units_to
from xclim.sdba import properties, measures, construct_moving_yearly_window, unpack_moving_yearly_window
from xclim.core.formatting import update_xclim_history
from xclim.sdba.measures import rmse

from xscen.checkups import fig_compare_and_diff, fig_bias_compare_and_diff
from xscen.catalog import ProjectCatalog, parse_directory, parse_from_ds, DataCatalog
from xscen.extraction import search_data_catalogs, extract_dataset
from xscen.io import save_to_zarr, rechunk
from xscen.config import CONFIG, load_config
from xscen.common import minimum_calendar, translate_time_chunk, stack_drop_nans, unstack_fill_nan, maybe_unstack
from xscen.regridding import regrid
from xscen.biasadjust import train, adjust
from xscen.scr_utils import measure_time, send_mail, send_mail_on_exit, timeout

# Load configuration
load_config('paths_ESPO-G.yml', 'config_ESPO-G.yml', verbose=(__name__ == '__main__'), reset=True)
logger = logging.getLogger('xscen')
workdir = Path(CONFIG['paths']['workdir'])
exec_wdir = Path(CONFIG['paths']['exec_workdir'])
refdir = Path(CONFIG['paths']['refdir'])
# TODO: before doing it for real, change the mode, but for testing it is in overwrite
mode = 'o'

def compute_properties(sim, ref, period):
    # TODO add more diagnostics, xclim.sdba and from Yannick (R2?)
    nan_count = sim.to_array().isnull().sum('time').mean('variable')
    hist = sim.sel(time=period)
    ref = ref.sel(time=period)

    # Je load deux des variables pour essayer d'éviter les KilledWorker et Timeout
    out = xr.Dataset(data_vars={

        'tx_mean_rmse': rmse(atmos.tx_mean(hist.tasmax, freq='MS').chunk({'time': -1}),
                             atmos.tx_mean(ref.tasmax, freq='MS').chunk({'time': -1})),
        'tn_mean_rmse': rmse(atmos.tn_mean(tasmin=hist.tasmin, freq='MS').chunk({'time': -1}),
                             atmos.tn_mean(tasmin=ref.tasmin, freq='MS').chunk({'time': -1})),
        'prcptot_rmse': rmse(atmos.precip_accumulation(hist.pr, freq='MS').chunk({'time': -1}),
                             atmos.precip_accumulation(ref.pr, freq='MS').chunk({'time': -1})),
        'nan_count': nan_count,
    })

    return out

def save_move_update(ds, name, region_name, init_dir, final_dir, encoding=CONFIG['custom']['encoding']):
    save_to_zarr(ds, f"{init_dir}/ref_{region_name}_360day.zarr",
                 compute=True, encoding=encoding, mode=mode)
    shutil.move(f"{init_dir}/ref_{region_name}_{name}.zarr",
                f"{final_dir}/ref_{region_name}_{name}.zarr")
    pcat.update_from_ds(ds=ds, path=f"{final_dir}/ref_{region_name}_{name}.zarr",
                        info_dict={'calendar': name})


if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    dask_perf_file = Path(CONFIG['paths']['reports']) / 'perf_report_template.html'
    dask_perf_file.parent.mkdir(exist_ok=True, parents=True)
    atexit.register(send_mail_on_exit, subject=CONFIG['scr_utils']['subject'])

    # defining variables
    fut_period = slice(*map(str, CONFIG['custom']['future_period']))
    ref_period = slice(*map(str, CONFIG['custom']['ref_period']))
    sim_period = slice(*map(str, CONFIG['custom']['sim_period']))
    check_period = slice(*map(str, CONFIG['custom']['check_period']))


    ref_project = CONFIG['extraction']['ref_project']

    # initialize Project Catalog
    if "initialize_pcat" in CONFIG["tasks"]:
        pcat = ProjectCatalog.create(CONFIG['paths']['project_catalog'], project=CONFIG['project'], overwrite=True)

    # load project catalog
    pcat = ProjectCatalog(CONFIG['paths']['project_catalog'])

    # ---MAKEREF---
    for region_name, region_dict in CONFIG['custom']['regions'].items():
        if (
                "makeref" in CONFIG["tasks"]
                and not pcat.exists_in_cat(domain=region_name, processing_level='extracted', project=ref_project)
        ):
            with (
                    Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws),
                    #Client(n_workers=3, threads_per_worker=5, memory_limit="15GB", **daskkws),
                    measure_time(name='makeref', logger=logger)
            ):

                # search
                cat_ref = search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

                # extract
                dc = cat_ref.popitem()[1]
                ds_ref = extract_dataset(catalog=dc,
                                         region=region_dict,
                                         **CONFIG['extraction']['reference']['extract_dataset']
                                         )
                #necessary because era5-land data is not exactly the same for all variables right now, so chunks are wrong
                ds_ref = ds_ref.chunk({'lat':225, 'lon':252, 'time' :168})

                dref_ref = ds_ref.drop_vars('dtr')  # time period already cut in extract
                ds_ref_props_nan_count = dref_ref.to_array().isnull().chunk({'time': -1}).sum('time').mean('variable').chunk(
                    {'lon': -1, 'lat': -1})
                save_to_zarr(ds_ref_props_nan_count.to_dataset(name='nan_count'), f"{exec_wdir}/ref_{region_name}_nancount.zarr",
                             compute=True, mode=mode)
                print('saved nan')

                if CONFIG['custom']['stack_drop_nans']:
                    variables = list(CONFIG['extraction']['reference']['search_data_catalogs'][
                                         'variables_and_timedeltas'].keys())
                    ds_ref = stack_drop_nans(
                        ds_ref,
                        ds_ref[variables[0]].isel(time=130, drop=True).notnull(),
                        to_file=f'{refdir}/coords_{region_name}.nc'
                    )
                ds_ref = ds_ref.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_ref.dims})

                # convert calendars
                ds_refnl = convert_calendar(ds_ref, "noleap")
                ds_ref360 = convert_calendar(ds_ref, "360_day", align_on="year")
                print('convert calendars')



                save_to_zarr(ds_ref, f"{exec_wdir}/ref_{region_name}_default.zarr",
                             compute=True, encoding=CONFIG['custom']['encoding'], mode=mode)
                save_to_zarr(ds_refnl, f"{exec_wdir}/ref_{region_name}_noleap.zarr",
                             compute=True, encoding=CONFIG['custom']['encoding'], mode=mode)
                #save_to_zarr(ds_ref360, f"{exec_wdir}/ref_{region_name}_360day.zarr",
                             #compute=True, encoding=CONFIG['custom']['encoding'], mode=mode)
                
                print('saved')
                ds_ref_props_nan_count = xr.open_zarr(f"{exec_wdir}/ref_{region_name}_nancount.zarr", decode_timedelta=False).load()
                print('load')
                fig, ax = plt.subplots(figsize=(10, 10))
                cmap = plt.cm.winter.copy()
                cmap.set_under('white')
                ds_ref_props_nan_count.nan_count.plot(ax=ax, vmin=1, vmax=1000, cmap=cmap)
                ax.set_title(
                   f'Reference {region_name} - NaN count \nmax {ds_ref_props_nan_count.nan_count.max().item()} out of {dref_ref.time.size}')
                plt.close('all')
                print('fig')

                #move from exec to tank
                shutil.move(f"{exec_wdir}/ref_{region_name}_nancount.zarr",f"{refdir}/ref_{region_name}_nancount.zarr")


                # update cat
                for ds, name in zip([ds_ref, ds_refnl, ds_ref360], ['default', 'noleap', '360day']):
                    shutil.move(f"{exec_wdir}/ref_{region_name}_{name}.zarr",
                                f"{refdir}/ref_{region_name}_{name}.zarr")
                    pcat.update_from_ds(ds=ds, path=f"{refdir}/ref_{region_name}_{name}.zarr",
                                        info_dict= {'calendar': name})
                print('update')

                send_mail(
                    subject=f'Reference for region {region_name} - Success',
                    msg=f"Action 'makeref' succeeded for region {region_name}.",
                    attachments=[fig]
                )

        if (
                "makerefSplit" in CONFIG["tasks"]
                #and not pcat.exists_in_cat(domain=region_name, processing_level='extracted', project=ref_project)
        ):
            if not pcat.exists_in_cat(domain=region_name, calendar='default', project=ref_project):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
                    # search
                    cat_ref = search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

                    # extract
                    dc = cat_ref.popitem()[1]
                    ds_ref = extract_dataset(catalog=dc,
                                             region=region_dict,
                                             **CONFIG['extraction']['reference']['extract_dataset']
                                             )
                    print('extract')
                    # necessary because era5-land data is not exactly the same for all variables right now, so chunks are wrong
                    ds_ref = ds_ref.chunk({'lat': 225, 'lon': 252, 'time': 168})

                    if CONFIG['custom']['stack_drop_nans']:
                        variables = list(CONFIG['extraction']['reference']['search_data_catalogs'][
                                             'variables_and_timedeltas'].keys())
                        ds_ref = stack_drop_nans(
                            ds_ref,
                            ds_ref[variables[0]].isel(time=130, drop=True).notnull(),
                            to_file=f'{refdir}/coords_{region_name}.nc'
                        )
                    ds_ref = ds_ref.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_ref.dims})
                    print('init')

                    save_move_update(ds=ds_ref, name='default', region_name=region_name, init_dir=exec_wdir, final_dir=refdir)
                    print('default')

            if not pcat.exists_in_cat(domain=region_name, calendar='noleap', project=ref_project):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):

                    ds_ref = pcat.search(project=ref_project,calendar='default',domain=region_name).to_dataset_dict().popitem()[1]

                    # convert calendars
                    ds_refnl = convert_calendar(ds_ref, "noleap")
                    save_move_update(ds=ds_refnl, name='noleap', region_name=region_name, init_dir=exec_wdir,final_dir=refdir)
                    print('nl')
            if not pcat.exists_in_cat(domain=region_name, calendar='noleap', project=ref_project):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)) :

                    ds_ref = pcat.search(project=ref_project,calendar='default',domain=region_name).to_dataset_dict().popitem()[1]

                    ds_ref360 = convert_calendar(ds_ref, "360_day", align_on="year")
                    save_move_update(ds=ds_ref360, name='360day', region_name=region_name, init_dir=exec_wdir,final_dir= refdir)
                    print('360')

            if  not pcat.exists_in_cat(domain=region_name, processing_level='properties', project=ref_project):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)) :

                    # search
                    cat_ref = search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

                    # extract
                    dc = cat_ref.popitem()[1]
                    ds_ref = extract_dataset(catalog=dc,
                                             region=region_dict,
                                             **CONFIG['extraction']['reference']['extract_dataset']
                                             )
                    print('extract')
                    # necessary because era5-land data is not exactly the same for all variables right now, so chunks are wrong
                    ds_ref = ds_ref.chunk({'lat': 225, 'lon': 252, 'time': 168})

                    dref_ref = ds_ref.drop_vars('dtr')  # time period already cut in extract
                    ds_ref_props_nan_count = dref_ref.to_array().isnull().chunk({'time': -1}).sum('time').mean(
                        'variable').chunk({'lon': -1, 'lat': -1})
                    ds_ref_props_nan_count.attrs.update(ds_ref.attrs)
                    save_to_zarr(ds_ref_props_nan_count.to_dataset(name='nan_count'),
                                 f"{exec_wdir}/ref_{region_name}_nancount.zarr",
                                 compute=True, mode=mode)

                    ds_ref_props_nan_count = xr.open_zarr(f"{exec_wdir}/ref_{region_name}_nancount.zarr",decode_timedelta=False).load()
                    print('load')
                    fig, ax = plt.subplots(figsize=(10, 10))
                    cmap = plt.cm.winter.copy()
                    cmap.set_under('white')
                    ds_ref_props_nan_count.nan_count.plot(ax=ax, vmin=1, vmax=1000, cmap=cmap)
                    ax.set_title(
                        f'Reference {region_name} - NaN count \nmax {ds_ref_props_nan_count.nan_count.max().item()} out of {dref_ref.time.size}')
                    plt.close('all')
                    print('fig')

                    send_mail(
                        subject=f'Reference for region {region_name} - Success',
                        msg=f"Action 'makeref' succeeded for region {region_name}.",
                        attachments=[fig]
                    )

                    shutil.move(f"{exec_wdir}/ref_{region_name}_nancount.zarr",
                                f"{refdir}/ref_{region_name}_nancount.zarr")
                    pcat.update_from_ds(ds=ds_ref_props_nan_count, path=f"{refdir}/ref_{region_name}_{name}.zarr",
                                        info_dict={'processing_level': 'properties'})




    for sim_id in CONFIG['ids']:
        for exp in CONFIG['experiments']:
            sim_id = sim_id.replace('EXPERIMENT',exp)
            for region_name, region_dict in CONFIG['custom']['regions'].items():
                if not pcat.exists_in_cat(domain=region_name, processing_level='final', id=sim_id):

                    fmtkws = {'region_name': region_name,
                              'sim_id': sim_id}
                    print(fmtkws)

                    # ---REGRID---
                    if (
                            "regrid" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, processing_level='regridded', id=sim_id)
                    ):
                        with (
                                #Client(n_workers=5, threads_per_worker=3, memory_limit="10GB", **daskkws),
                                Client(n_workers=2, threads_per_worker=3, memory_limit="25GB", **daskkws),
                                measure_time(name='regrid', logger=logger)
                        ):
                            # search the data that we need
                            cat_sim = search_data_catalogs(**CONFIG['extraction']['simulations']['search_data_catalogs'])

                            # extract
                            dc = cat_sim[sim_id]
                            ds_sim = extract_dataset(catalog=dc,
                                                     **CONFIG['extraction']['simulations']['extract_dataset'],
                                                     )
                            ds_sim['time'] = ds_sim.time.dt.floor('D')

                            # get reference
                            ds_refnl = pcat.search(project=ref_project,
                                                   calendar='noleap',
                                                   domain=region_name).to_dataset_dict().popitem()[1]

                            # regrid
                            ds_sim_regrid = regrid(
                                ds=ds_sim,
                                ds_grid=ds_refnl,
                                **CONFIG['regrid']
                            )

                            # chunk time dim
                            ds_sim_regrid = ds_sim_regrid.chunk(translate_time_chunk({'time': '4year'},
                                                                                     get_calendar(ds_sim_regrid),
                                                                                     ds_sim_regrid.time.size
                                                                                     )
                                                                )

                            # save to zarr
                            path_rg = f"{exec_wdir}/{sim_id}_regridded.zarr"
                            save_to_zarr(ds=ds_sim_regrid,
                                         filename=path_rg,
                                         encoding=CONFIG['custom']['encoding'],
                                         compute=True,
                                         mode=mode
                                         )
                            shutil.move(f"{exec_wdir}/{sim_id}_regridded.zarr", f"{workdir}/{sim_id}_regridded.zarr")
                            pcat.update_from_ds(ds=ds_sim_regrid, path=path_rg)

                    #  ---RECHUNK---
                    if (
                            "rechunk" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, processing_level='regridded_and_rechunked',id=sim_id)
                    ):
                        with (
                                Client(n_workers=2, threads_per_worker=5, memory_limit="18GB", **daskkws),
                                measure_time(name=f'rechunk', logger=logger)
                        ):
                            path_rc = f"{exec_wdir}/{sim_id}_regchunked.zarr"
                            rechunk(path_in=f"{workdir}/{sim_id}_regridded.zarr",
                                    path_out=path_rc,
                                    chunks_over_dim=CONFIG['custom']['chunks'],
                                    **CONFIG['rechunk'],
                                    overwrite=True)
                            shutil.move(f"{exec_wdir}/{sim_id}_regchunked.zarr",f"{workdir}/{sim_id}_regchunked.zarr")

                            ds_sim_rechunked = xr.open_zarr(f"{workdir}/{sim_id}_regchunked.zarr", decode_timedelta=False)

                            pcat.update_from_ds(ds=ds_sim_rechunked,
                                                path=f"{workdir}/{sim_id}_regchunked.zarr",
                                                info_dict={'processing_level': 'regridded_and_rechunked'})

                    # --- SIM PROPERTIES ---
                    if ("simproperties" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, id=f"{sim_id}_simprops")
                    ):
                        with (
                                Client(n_workers=9, threads_per_worker=3, memory_limit="7GB", **daskkws),
                                measure_time(name=f'simproperties', logger=logger),
                                timeout(3600, task='simproperties')
                        ):
                            ds_sim = pcat.search(id=sim_id,
                                                 processing_level='regridded_and_rechunked',
                                                 domain=region_name).to_dataset_dict().popitem()[1]
                            ds_sim = ds_sim.chunk({'time': -1})

                            simcal = get_calendar(ds_sim)
                            ds_ref = pcat.search(project=ref_project,
                                                 calendar= simcal,
                                                 domain=region_name).to_dataset_dict().popitem()[1]

                            ds_sim_props = compute_properties(ds_sim, ds_ref, check_period)
                            ds_sim_props.attrs.update(ds_sim.attrs)

                            path_sim = Path(CONFIG['paths']['checkups'].format(region_name=region_name, sim_id=sim_id, step='sim'))
                            path_sim.parent.mkdir(exist_ok=True, parents=True)

                            path_sim_exec = f"{exec_wdir}/{path_sim.name}"

                            save_to_zarr(ds=ds_sim_props,
                                         filename=path_sim_exec,
                                         mode=mode,
                                         itervar=True)
                            shutil.move(path_sim_exec, path_sim)

                            logger.info('Sim properties computed, painting nan count and sending plot.')

                            ds_sim_props_unstack = unstack_fill_nan(ds_sim_props, coords=refdir / f'coords_{region_name}.nc')
                            nan_count = ds_sim_props_unstack.nan_count.load()

                            fig, ax = plt.subplots(figsize=(12, 8))
                            cmap = plt.cm.winter.copy()
                            cmap.set_under('white')
                            nan_count.plot(ax=ax, vmin=1, vmax=1000, cmap=cmap)
                            ax.set_title(
                                f'Raw simulation {sim_id} {region_name} - NaN count \nmax {nan_count.max().item()} out of {ds_sim.time.size}')
                            send_mail(
                                subject=f'Properties of {sim_id} {region_name} - Success',
                                msg=f"Action 'simproperties' succeeded.",
                                attachments=[fig]
                            )
                            plt.close('all')

                            pcat.update_from_ds(ds=ds_sim_props,
                                                info_dict={'id': f"{sim_id}_simprops",
                                                           'processing_level': 'properties'},
                                                path=str(path_sim))

                    # ---BIAS ADJUST---
                    for var, conf in CONFIG['biasadjust']['variables'].items():

                        # ---TRAIN ---
                        if (
                                "train" in CONFIG["tasks"]
                                and not pcat.exists_in_cat(domain=region_name, id=f"{sim_id}_training_{var}")
                        ):
                            with (
                                    Client(n_workers=9, threads_per_worker=3, memory_limit="7GB", **daskkws),
                                    measure_time(name=f'train {var}', logger=logger)
                            ):
                                # load hist ds (simulation)
                                ds_hist = pcat.search(id=sim_id,domain=region_name, processing_level='regridded_and_rechunked').to_dataset_dict().popitem()[1]

                                # load ref ds
                                # choose right calendar
                                simcal = get_calendar(ds_hist)
                                refcal = minimum_calendar(simcal,
                                                          CONFIG['custom']['maximal_calendar'])
                                ds_ref = pcat.search(project = ref_project,
                                                     calendar=refcal,
                                                     domain=region_name).to_dataset_dict().popitem()[1]

                                # training
                                ds_tr = train(dref=ds_ref,
                                              dhist=ds_hist,
                                              var=[var],
                                              **conf['training_args'])

                                path_tr = f"{workdir}/{sim_id}_{var}_training.zarr"
                                path_tr_exec = f"{exec_wdir}/{sim_id}_{var}_training.zarr"


                                save_to_zarr(ds=ds_tr,
                                             filename=path_tr_exec,
                                             mode='o')
                                shutil.move(path_tr_exec, path_tr )
                                pcat.update_from_ds(ds=ds_tr,
                                                    info_dict={'id': f"{sim_id}_training_{var}",
                                                               'domain': region_name,
                                                               'processing_level': "training",
                                                               'frequency': ds_hist.attrs['cat/frequency']
                                                                },
                                                    path=path_tr)

                        # ---ADJUST---
                        if (
                                "adjust" in CONFIG["tasks"]
                                and not pcat.exists_in_cat(domain=region_name, id=sim_id, processing_level='biasadjusted',
                                                           variable=var)
                        ):
                            with (
                                    Client(n_workers=6, threads_per_worker=3, memory_limit="10GB", **daskkws),
                                    measure_time(name=f'adjust {var}', logger=logger)
                            ):
                                # load sim ds
                                ds_sim = pcat.search(id=sim_id,
                                                     processing_level='regridded_and_rechunked',
                                                     domain=region_name).to_dataset_dict().popitem()[1]
                                ds_tr = pcat.search(id=f'{sim_id}_training_{var}', domain=region_name).to_dataset_dict().popitem()[1]

                                ds_scen = adjust(dsim=ds_sim,
                                                 dtrain=ds_tr,
                                                 **conf['adjusting_args'])
                                path_adj = f"{workdir}/{sim_id}_{var}_adjusted.zarr"
                                path_adj_exec = f"{exec_wdir}/{sim_id}_{var}_adjusted.zarr"
                                ds_scen.lat.encoding.pop('chunks')
                                ds_scen.lon.encoding.pop('chunks')
                                save_to_zarr(ds=ds_scen,
                                             filename=path_adj_exec,
                                             mode='o')
                                shutil.move(path_adj_exec, path_adj)
                                pcat.update_from_ds(ds=ds_scen, path=path_adj)

                    # ---CLEAN UP ---
                    if (
                            "clean_up" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, id=sim_id, processing_level='cleaned_up')
                    ):
                        with (
                                Client(n_workers=4, threads_per_worker=3, memory_limit="15GB", **daskkws),
                                measure_time(name=f'cleanup', logger=logger)
                        ):
                            cat = search_data_catalogs(**CONFIG['clean_up']['search_data_catalogs'],
                                                       other_search_criteria= { 'id': [sim_id],
                                                                                'processing_level':["biasadjusted"],
                                                                                'domain': region_name}
                                                        )
                            dc = cat.popitem()[1]
                            ds = extract_dataset(catalog=dc,
                                                 to_level='cleaned_up'
                                                      )
                            ds.attrs['cat/id']=sim_id

                            ds['pr']=convert_units_to(ds.pr, 'mm d-1')

                            # remove all global attrs that don't come from the catalogue
                            for attr in list(ds.attrs.keys()):
                                if attr[:4] != 'cat/':
                                    del ds.attrs[attr]

                            # unstack nans
                            if CONFIG['custom']['stack_drop_nans']:
                                ds = unstack_fill_nan(ds, coords=f"{refdir}/coords_{region_name}.nc")
                                ds = ds.chunk({d: CONFIG['custom']['chunks'][d] for d in ds.dims})

                            # add final attrs
                            for var, attrs in CONFIG['clean_up']['attrs'].items():
                                obj = ds if var == 'global' else ds[var]
                                for attrname, attrtmpl in attrs.items():
                                    obj.attrs[attrname] = attrtmpl.format( **fmtkws)

                            # only keep specific var attrs
                            for var in ds.data_vars.values():
                                for attr in list(var.attrs.keys()):
                                    if attr not in CONFIG['clean_up']['final_attrs_names']:
                                        del var.attrs[attr]
                            path_cu = f"{workdir}/{sim_id}_cleaned_up.zarr"
                            path_cu_exec = f"{exec_wdir}/{sim_id}_cleaned_up.zarr"
                            save_to_zarr(ds=ds,
                                         filename=path_cu_exec,
                                         mode='o')
                            shutil.move(path_cu_exec, path_cu)
                            pcat.update_from_ds(ds=ds, path=path_cu,
                                                info_dict= {'processing_level': 'cleaned_up'})

                    # ---FINAL ZARR ---
                    if (
                            "final_zarr" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, id=sim_id, processing_level='final',
                                                       format='zarr')
                    ):
                        with (
                                Client(n_workers=3, threads_per_worker=5, memory_limit="20GB", **daskkws),
                                measure_time(name=f'final zarr rechunk', logger=logger)
                        ):
                            fi_path = Path(f"{CONFIG['paths']['output']}".format(**fmtkws))
                            fi_path.parent.mkdir(exist_ok=True, parents=True)

                            fi_path_exec = f"{exec_wdir}/{fi_path.name}"

                            rechunk(path_in=f"{workdir}/{sim_id}_cleaned_up.zarr",
                                    path_out=fi_path_exec,
                                    chunks_over_dim=CONFIG['custom']['out_chunks'],
                                    **CONFIG['rechunk'],
                                    overwrite=True)
                            shutil.move(fi_path_exec, fi_path)
                            ds = xr.open_zarr(fi_path)
                            pcat.update_from_ds(ds=ds, path=str(fi_path), info_dict= {'processing_level': 'final'})

                    # --- SCEN PROPS ---
                    if (
                            "scenproperties" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, id=f"{sim_id}_scenprops")
                    ):
                        with (
                                Client(n_workers=9, threads_per_worker=3, memory_limit="7GB", **daskkws),
                                measure_time(name=f'scenprops', logger=logger),
                                timeout(5400, task='scenproperties')
                        ):
                            ds_scen = pcat.search(id=sim_id,processing_level='final', domain=region_name).to_dataset_dict().popitem()[1]


                            scen_cal = get_calendar(ds_scen)
                            ds_ref = maybe_unstack(
                                pcat.search(project = ref_project,
                                            calendar=scen_cal,
                                            domain=region_name).to_dataset_dict().popitem()[1],
                                stack_drop_nans=CONFIG['custom']['stack_drop_nans'],
                                coords= refdir / f'coords_{region_name}.nc',
                                rechunk={d: CONFIG['custom']['out_chunks'][d] for d in ['lat', 'lon']}
                            )

                            ds_scen_props = compute_properties(ds_scen, ds_ref, check_period)
                            ds_scen_props.attrs.update(ds_scen.attrs)

                            path_scen = CONFIG['paths']['checkups'].format(region_name=region_name, sim_id=sim_id, step='scen')
                            path_scen_exec = f"{exec_wdir}/{path_scen.name}"

                            save_to_zarr(ds=ds_scen_props,filename=path_scen_exec,mode=mode,itervar=True)
                            shutil.move(path_scen_exec, path_scen)

                            pcat.update_from_ds(ds=ds_scen_props,
                                                info_dict={'id': f"{sim_id}_scenprops",
                                                           'processing_level': 'properties'},
                                                path=str(path_scen))

                    # --- CHECK UP ---
                    if "check_up" in CONFIG["tasks"]:
                        with (
                                Client(n_workers=6, threads_per_worker=3, memory_limit="10GB", **daskkws),
                                measure_time(name=f'checkup', logger=logger)
                        ):

                            ref = pcat.search(project = ref_project,
                                              processing_level='properties',
                                              domain=region_name).to_dataset_dict().popitem()[1].load()
                            sim = maybe_unstack(
                                pcat.search(id=f'{sim_id}_simprops', domain=region_name).to_dataset_dict().popitem()[1],
                                coords= refdir / f'coords_{region_name}.nc',
                                stack_drop_nans=CONFIG['custom']['stack_drop_nans']
                            ).load()

                            scen = pcat.search(id=f'{sim_id}_scenprops', domain=region_name).to_dataset_dict().popitem()[1].load()

                            fig_dir = Path(CONFIG['paths']['checkfigs'].format(**fmtkws))
                            fig_dir.mkdir(exist_ok=True, parents=True)
                            paths = []

                            # NaN count
                            fig_compare_and_diff(
                                sim.nan_count.rename('sim'),
                                scen.nan_count.rename('scen'),
                                title='Comparing NaN counts.'
                            ).savefig(fig_dir / 'Nan_count.png')
                            paths.append(fig_dir / 'Nan_count.png')

                            for var in [ 'tx_mean_rmse', 'tn_mean_rmse', 'prcptot_rmse']:
                                fig_compare_and_diff(
                                    sim[var], scen[var], op = "improvement"
                                ).savefig(fig_dir / f'{var}_compare.png')
                                paths.append(fig_dir / f'{var}_compare.png')

                            send_mail(
                                subject=f"{sim_id}/{region_name} - Succès",
                                msg=f"Toutes les étapes demandées pour la simulation {sim_id}/{region_name} ont été accomplies.",
                                attachments=paths
                            )
                            plt.close('all')
                            # when region is done erase workdir
                            shutil.rmtree(workdir)
                            os.mkdir(workdir)

            if (
                    "concat" in CONFIG["tasks"]
                    and not pcat.exists_in_cat(domain='concat_regions', id=sim_id, processing_level='final', format='zarr')
            ):
                dskconf.set(num_workers=12)
                ProgressBar().register()

                print(f'Contenating {sim_id}.')

                list_dsR = []
                for region_name in CONFIG['custom']['regions']:
                    fmtkws = {'region_name': region_name,
                              'sim_id': sim_id}

                    dsR = pcat.search(id=sim_id,
                                      domain=region_name,
                                      processing_level='final').to_dataset_dict().popitem()[1]

                    list_dsR.append(dsR)

                dsC = xr.concat(list_dsR, 'lat')

                dsC.attrs['title'] = f"ESPO-G6 v1.0.0 - {sim_id}"
                dsC.attrs['cat/domain'] = f"NAM"
                dsC.attrs.pop('intake_esm_dataset_key')

                dsC_path = CONFIG['paths']['concat_output'].format(sim_id=sim_id)
                dsC.attrs.pop('cat/path')
                # TODO: change this with real regions
                dsC = dsC.chunk({'lat':2, 'lon':2, 'time':1460})
                save_to_zarr(ds=dsC,
                             filename=dsC_path,
                             mode='o')
                pcat.update_from_ds(ds=dsC, info_dict={'domain': 'concat_regions'},
                                    path=dsC_path)

                print('All concatenations done for today.')
