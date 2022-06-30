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
import dask

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

from utils import compute_properties, save_move_update, calculate_properties, save_diagnotics

# Load configuration
load_config('paths_ESPO-G.yml', 'config_ESPO-G.yml', verbose=(__name__ == '__main__'), reset=True)
logger = logging.getLogger('xscen')
workdir = Path(CONFIG['paths']['workdir'])
exec_wdir = Path(CONFIG['paths']['exec_workdir'])
regriddir = Path(CONFIG['paths']['regriddir'])
refdir = Path(CONFIG['paths']['refdir'])

# TODO: before doing it for real, change the mode, but for testing it is in overwrite
mode = 'o'





if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
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
                and not pcat.exists_in_cat(domain=region_name, processing_level='properties', project=ref_project)
        ):

            # default
            if not pcat.exists_in_cat(domain=region_name, project=ref_project, calendar='default'):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
                    # search
                    cat_ref = search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

                    # extract
                    dc = cat_ref.popitem()[1]
                    ds_ref = extract_dataset(catalog=dc,
                                             region=region_dict,
                                             **CONFIG['extraction']['reference']['extract_dataset']
                                             )
                    # necessary because era5-land data is not exactly the same for all variables right now, so chunks are wrong
                    ds_ref = ds_ref.chunk({'lat': 225, 'lon': 252, 'time': 168})

                    #stack
                    if CONFIG['custom']['stack_drop_nans']:
                        variables = list(CONFIG['extraction']['reference']['search_data_catalogs'][
                                             'variables_and_timedeltas'].keys())
                        ds_ref = stack_drop_nans(
                            ds_ref,
                            ds_ref[variables[0]].isel(time=130, drop=True).notnull(),
                            to_file=f'{refdir}/coords_{region_name}.nc'
                        )
                    ds_ref = ds_ref.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_ref.dims})

                    save_move_update(ds=ds_ref,
                                     pcat = pcat,
                                     init_path=f"{exec_wdir}/ref_{region_name}_default.zarr",
                                     final_path=f"{refdir}/ref_{region_name}_default.zarr",
                                     info_dict={'calendar': 'default'})

            # noleap
            if not pcat.exists_in_cat(domain=region_name, calendar='noleap', project=ref_project):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):

                    ds_ref = pcat.search(project=ref_project,calendar='default',domain=region_name).to_dataset_dict().popitem()[1]

                    # convert calendars
                    ds_refnl = convert_calendar(ds_ref, "noleap")
                    save_move_update(ds=ds_refnl,
                                     pcat=pcat,
                                     init_path=f"{exec_wdir}/ref_{region_name}_noleap.zarr",
                                     final_path=f"{refdir}/ref_{region_name}_noleap.zarr",
                                     info_dict={'calendar': 'noleap'})
            # 360day
            if not pcat.exists_in_cat(domain=region_name, calendar='360day', project=ref_project):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)) :

                    ds_ref = pcat.search(project=ref_project,calendar='default',domain=region_name).to_dataset_dict().popitem()[1]

                    ds_ref360 = convert_calendar(ds_ref, "360_day", align_on="year")
                    save_move_update(ds=ds_ref360,
                                     pcat=pcat,
                                     init_path=f"{exec_wdir}/ref_{region_name}_360day.zarr",
                                     final_path=f"{refdir}/ref_{region_name}_360day.zarr",
                                     info_dict={'calendar': '360day'})

            # nan_count
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
                    # necessary because era5-land data is not exactly the same for all variables right now, so chunks are wrong
                    ds_ref = ds_ref.chunk({'lat': 225, 'lon': 252, 'time': 168})

                    #drop to make faster
                    dref_ref = ds_ref.drop_vars('dtr')

                    #nan count
                    ds_ref_props_nan_count = dref_ref.to_array().isnull().chunk({'time': -1}).sum('time').mean(
                        'variable').chunk({'lon': -1, 'lat': -1})
                    ds_ref_props_nan_count = ds_ref_props_nan_count.to_dataset(name='nan_count')
                    ds_ref_props_nan_count.attrs.update(ds_ref.attrs)

                    #save
                    save_to_zarr(ds_ref_props_nan_count,
                                 f"{exec_wdir}/ref_{region_name}_nancount.zarr",
                                 compute=True, mode=mode)

                    # diagnostics
                    if 'diagnostics' in CONFIG['tasks']:
                        calculate_properties(ds=dref_ref, pcat=pcat, step='ref')

                    # plot and email
                    ds_ref_props_nan_count = xr.open_zarr(f"{exec_wdir}/ref_{region_name}_nancount.zarr",decode_timedelta=False).load()
                    fig, ax = plt.subplots(figsize=(10, 10))
                    cmap = plt.cm.winter.copy()
                    cmap.set_under('white')
                    ds_ref_props_nan_count.nan_count.plot(ax=ax, vmin=1, vmax=1000, cmap=cmap)
                    ax.set_title(
                        f'Reference {region_name} - NaN count \nmax {ds_ref_props_nan_count.nan_count.max().item()} out of {dref_ref.time.size}')
                    plt.close('all')

                    send_mail(
                        subject=f'Reference for region {region_name} - Success',
                        msg=f"Action 'makeref' succeeded for region {region_name}.",
                        attachments=[fig]
                    )

                    # move and update
                    shutil.move(f"{exec_wdir}/ref_{region_name}_nancount.zarr",
                                f"{refdir}/ref_{region_name}_nancount.zarr")
                    pcat.update_from_ds(ds=ds_ref_props_nan_count, path=f"{refdir}/ref_{region_name}_nancount.zarr",
                                        info_dict={'processing_level': 'properties'})




    for sim_id in CONFIG['ids']:
        for exp in CONFIG['experiments']:
            sim_id = sim_id.replace('EXPERIMENT',exp)
            for region_name, region_dict in CONFIG['custom']['regions'].items():

                fmtkws = {'region_name': region_name,
                          'sim_id': sim_id}
                print(fmtkws)
                final = {'check_up': dict(domain=region_name, processing_level='final', id=sim_id),
                         'diagnostics': dict(domain=region_name, processing_level='diag_scen', id=sim_id)}
                if not pcat.exists_in_cat(**final[CONFIG["tasks"][-2]]):
                    # ---CUT---
                    if (
                            "cut" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, processing_level='cut', id=sim_id)
                    ):
                        with (
                                Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws),
                                measure_time(name='cut', logger=logger),
                                timeout(18000, task='cut')
                        ):
                            # search the data that we need
                            cat_sim = search_data_catalogs(
                                **CONFIG['extraction']['simulations']['search_data_catalogs'])

                            # extract
                            dc = cat_sim[sim_id]
                            region_dict['buffer']=1.5
                            ds_sim = extract_dataset(catalog=dc,
                                                     region=region_dict,
                                                     **CONFIG['extraction']['simulations']['extract_dataset'],
                                                     )
                            ds_sim['time'] = ds_sim.time.dt.floor('D')

                            # need lat and lon -1 for the regrid
                            ds_sim = ds_sim.chunk(CONFIG['cut']['chunks'])

                            # save to zarr
                            path_cut_exec = f"{exec_wdir}/{sim_id}_{region_name}_cut.zarr"
                            path_cut = f"{workdir}/{sim_id}_{region_name}_cut.zarr"

                            save_move_update(ds=ds_sim,
                                             pcat=pcat,
                                             init_path=path_cut_exec,
                                             final_path=path_cut,
                                             info_dict={'processing_level':'cut'})
                    # ---REGRID---
                    if (
                            "regrid" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, processing_level='regridded', id=sim_id)
                    ):
                        with (
                                Client(n_workers=5, threads_per_worker=3, memory_limit="10GB", **daskkws),
                                measure_time(name='regrid', logger=logger),
                                timeout(18000, task='regrid')
                        ):
                            #get sim and ref
                            ds_sim = pcat.search(id=sim_id,
                                                 processing_level='cut',
                                                 domain=region_name).to_dataset_dict().popitem()[1]
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

                            # save
                            save_move_update(ds=ds_sim_regrid,
                                             pcat=pcat,
                                             init_path=f"{exec_wdir}/{sim_id}_{region_name}_regridded.zarr",
                                             final_path=f"{workdir}/{sim_id}_{region_name}_regridded.zarr",
                                             )

                    #  ---RECHUNK---
                    if (
                            "rechunk" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, processing_level='regridded_and_rechunked',id=sim_id)
                    ):
                        with (
                                Client(n_workers=2, threads_per_worker=5, memory_limit="18GB", **daskkws),
                                measure_time(name=f'rechunk', logger=logger),
                                timeout(18000, task='rechunk')
                        ):
                            #rechunk in exec
                            path_rc = f"{exec_wdir}/{sim_id}_{region_name}_regchunked.zarr"
                            rechunk(path_in=f"{workdir}/{sim_id}_{region_name}_regridded.zarr",
                                    path_out=path_rc,
                                    chunks_over_dim=CONFIG['custom']['chunks'],
                                    **CONFIG['rechunk'],
                                    overwrite=True)
                            # move to workdir
                            shutil.move(f"{exec_wdir}/{sim_id}_{region_name}_regchunked.zarr",f"{workdir}/{sim_id}_{region_name}_regchunked.zarr")

                            ds_sim_rechunked = xr.open_zarr(f"{workdir}/{sim_id}_{region_name}_regchunked.zarr", decode_timedelta=False)
                            pcat.update_from_ds(ds=ds_sim_rechunked,
                                                path=f"{workdir}/{sim_id}_{region_name}_regchunked.zarr",
                                                info_dict={'processing_level': 'regridded_and_rechunked'})

                    # --- SIM PROPERTIES ---
                    if ("simproperties" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, id=f"{sim_id}_simprops")
                    ):
                        with (
                                Client(n_workers=4, threads_per_worker=3, memory_limit="7GB", **daskkws),
                                measure_time(name=f'simproperties', logger=logger),
                                timeout(6000, task='simproperties')
                        ):
                            #get sim and ref
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
                            print(path_sim_exec )
                            save_to_zarr(ds=ds_sim_props,
                                         filename=path_sim_exec,
                                         mode=mode,
                                         itervar=True)
                            print('test after save')
                            shutil.move(path_sim_exec, path_sim)

                            print('test after move')

                            logger.info('Sim properties computed, painting nan count and sending plot.')

                            ds_sim_props = xr.open_zarr('/scen3/jlavoie/ESPO-G6/checkup/checkup_CMIP6_ScenarioMIP_CMCC_CMCC-ESM2_ssp245_r1i1p1f1_global_middle_sim.zarr')
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
                                    #Client(n_workers=4, threads_per_worker=3, memory_limit="15GB", **daskkws),
                                    measure_time(name=f'train {var}', logger=logger),
                                    timeout(18000, task='train')
                            ):
                                # load hist ds (simulation)
                                ds_hist = pcat.search(id=sim_id,domain=region_name, processing_level='regridded_and_rechunked').to_dataset_dict().popitem()[1]

                                # load ref ds
                                # choose right calendar
                                simcal = get_calendar(ds_hist)
                                refcal = minimum_calendar(simcal, CONFIG['custom']['maximal_calendar'])
                                ds_ref = pcat.search(project = ref_project,
                                                     calendar=refcal,
                                                     domain=region_name).to_dataset_dict().popitem()[1]


                                # move to exec and reopen to help dask
                                save_to_zarr(ds_ref, f"{CONFIG['paths']['exec_workdir']}ds_ref.zarr", mode='o')
                                save_to_zarr(ds_hist, f"{CONFIG['paths']['exec_workdir']}ds_hist.zarr", mode='o')
                                ds_ref=xr.open_zarr(f"{CONFIG['paths']['exec_workdir']}ds_ref.zarr", decode_timedelta=False)
                                ds_hist=xr.open_zarr(f"{CONFIG['paths']['exec_workdir']}ds_hist.zarr", decode_timedelta=False)

                                # training
                                ds_tr = train(dref=ds_ref,
                                              dhist=ds_hist,
                                              var=[var],
                                              **conf['training_args'])


                                ds_tr.lat.encoding.pop('chunks')
                                ds_tr.lon.encoding.pop('chunks')

                                ds_tr = ds_tr.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_tr.dims
                                                     if d in CONFIG['custom']['chunks'].keys() })
                                save_move_update(ds=ds_tr,
                                                 pcat=pcat,
                                                 init_path=f"{exec_wdir}/{sim_id}_{region_name}_{var}_training.zarr",
                                                 final_path=f"{workdir}/{sim_id}_{region_name}_{var}_training.zarr",
                                                 encoding=None,
                                                 info_dict= {'id': f"{sim_id}_training_{var}",
                                                               'domain': region_name,
                                                               'processing_level': "training",
                                                               'frequency': ds_hist.attrs['cat/frequency']
                                                                })
                                shutil.rmtree(f"{CONFIG['paths']['exec_workdir']}ds_ref.zarr")
                                shutil.rmtree(f"{CONFIG['paths']['exec_workdir']}ds_hist.zarr")

                        # ---ADJUST---
                        if (
                                "adjust" in CONFIG["tasks"]
                                and not pcat.exists_in_cat(domain=region_name, id=sim_id, processing_level='biasadjusted',
                                                           variable=var)
                        ):
                            with (
                                    #Client(n_workers=6, threads_per_worker=3, memory_limit="10GB", **daskkws),
                                    Client(n_workers=5, threads_per_worker=3, memory_limit="12GB", **daskkws),
                                    measure_time(name=f'adjust {var}', logger=logger),
                                    timeout(18000, task='adjust')
                            ):
                                # load sim ds
                                ds_sim = pcat.search(id=sim_id,
                                                     processing_level='regridded_and_rechunked',
                                                     domain=region_name).to_dataset_dict().popitem()[1]
                                ds_tr = pcat.search(id=f'{sim_id}_training_{var}', domain=region_name).to_dataset_dict().popitem()[1]

                                # adjust
                                ds_scen = adjust(dsim=ds_sim,
                                                 dtrain=ds_tr,
                                                 **conf['adjusting_args'])

                                ds_scen.lat.encoding.pop('chunks')
                                ds_scen.lon.encoding.pop('chunks')

                                save_move_update(ds=ds_scen,
                                                 pcat=pcat,
                                                 encoding=None,
                                                 init_path=f"{exec_wdir}/{sim_id}_{region_name}_{var}_adjusted.zarr",
                                                 final_path=f"{workdir}/{sim_id}_{region_name}_{var}_adjusted.zarr",
                                                 )

                    # ---CLEAN UP ---
                    if (
                            "clean_up" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, id=sim_id, processing_level='cleaned_up')
                    ):
                        with (
                                #worked for middle
                                Client(n_workers=2, threads_per_worker=3, memory_limit="30GB", **daskkws),
                                measure_time(name=f'cleanup', logger=logger),
                                timeout(18000, task='clean_up')
                        ):
                            # get all adjusted data
                            cat = search_data_catalogs(**CONFIG['clean_up']['search_data_catalogs'],
                                                       other_search_criteria= { 'id': [sim_id],
                                                                                'processing_level':["biasadjusted"],
                                                                                'domain': region_name}
                                                        )
                            dc = cat.popitem()[1]
                            ds = extract_dataset(catalog=dc,
                                                 to_level='cleaned_up',
                                                 periods=CONFIG['custom']['sim_period']
                                                      )


                            #fix attrs
                            ds.attrs['cat/id']=sim_id
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


                            save_move_update(ds=ds,
                                             pcat=pcat,
                                             init_path=f"{exec_wdir}/{sim_id}_{region_name}_cleaned_up.zarr",
                                             final_path = f"{workdir}/{sim_id}_{region_name}_cleaned_up.zarr",
                                             info_dict = {'processing_level': 'cleaned_up'},
                                             encoding=None,
                                             itervar=True
                                             )

                    # ---FINAL ZARR ---
                    if (
                            "final_zarr" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, id=sim_id, processing_level='final',
                                                       format='zarr')
                    ):
                        with (
                                Client(n_workers=2, threads_per_worker=3, memory_limit="30GB", **daskkws),
                                measure_time(name=f'final zarr rechunk', logger=logger),
                                timeout(18000, task='final_zarr')
                        ):
                            dask.config.set({'temporary_directory': '/exec/jlavoie/tmp_eg6/'})
                            fi_path = Path(f"{CONFIG['paths']['output']}".format(**fmtkws))
                            fi_path.parent.mkdir(exist_ok=True, parents=True)
                            fi_path_exec = f"{exec_wdir}/{fi_path.name}"

                            shutil.copytree(f"{workdir}/{sim_id}_{region_name}_cleaned_up.zarr",
                                        f"{exec_wdir}/{sim_id}_{region_name}_cleaned_up.zarr")
                            # this busts the exec quota

                            #rechunk in exec and move to final path
                            rechunk(
                                path_in=f"{exec_wdir}/{sim_id}_{region_name}_cleaned_up.zarr",
                                #    path_in=f"{workdir}/{sim_id}_{region_name}_cleaned_up.zarr",
                                    path_out=fi_path_exec,
                                    chunks_over_dim=CONFIG['custom']['out_chunks'],
                                    **CONFIG['rechunk'],
                                    overwrite=True)

                            # ds_in = xr.open_zarr(f"{exec_wdir}/{sim_id}_{region_name}_cleaned_up.zarr", decode_timedelta=False)
                            # ds_in.lat.encoding.pop('chunks')
                            # ds_in.lon.encoding.pop('chunks')
                            # ds_in.time.encoding.pop('chunks')
                            # for d in ds_in.data_vars:
                            #     ds_in[d].encoding.pop('chunks')
                            # ds_out = ds_in.chunk({'time': 1460, 'lat': 50, 'lon': 50})
                            # save_to_zarr(ds_out, fi_path_exec, mode=mode, itervar=True)


                            shutil.move(fi_path_exec, fi_path)

                            #  move regridded to save it permantly
                            final_regrid_path= f"{regriddir}/{sim_id}_{region_name}_regchunked.zarr"
                            shutil.move(f"{workdir}/{sim_id}_{region_name}_regchunked.zarr",final_regrid_path  )
                            ds_sim = xr.open_zarr(final_regrid_path)
                            pcat.update_from_ds(ds=ds_sim, path = str(final_regrid_path),
                                                info_dict={'processing_level': 'regridded_and_rechunked'})

                            #save log
                            path_log = CONFIG['logging']['handlers']['file']['filename']
                            shutil.move(path_log, CONFIG['paths']['logging'].format(**fmtkws))

                            # when done erase workdir content
                            if workdir.exists() and workdir.is_dir() and CONFIG["tasks"][-2] == 'final_zarr':
                                shutil.rmtree(workdir)
                                os.mkdir(workdir)
                            if exec_wdir.exists() and exec_wdir.is_dir() and CONFIG["tasks"][-2] == 'final_zarr':
                                shutil.rmtree(exec_wdir)
                                os.mkdir(exec_wdir)



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

                            path_scen = Path(CONFIG['paths']['checkups'].format(region_name=region_name, sim_id=sim_id, step='scen'))

                            save_move_update(ds=ds_scen_props,
                                             pcat=pcat,
                                             init_path=f"{exec_wdir}/{path_scen.name}",
                                             final_path=str(path_scen),
                                             info_dict={'id': f"{sim_id}_scenprops",
                                                           'processing_level': 'properties'},
                                             encoding=None
                                             )

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

                    # ---DIAGNOSTICS ---
                    if (
                            "diagnostics" in CONFIG["tasks"]
                            and not pcat.exists_in_cat(domain=region_name, id=sim_id, processing_level='scen_diag')
                    ):
                        with (
                                Client(n_workers=3, threads_per_worker=5, memory_limit="20GB", **daskkws),
                                measure_time(name=f'diagnostics', logger=logger),
                                timeout(18000, task='diagnostics')
                        ):
                            #load initial data
                            ds_scen = pcat.search(processing_level='final',
                                                  id=sim_id,
                                                  domain=region_name
                                                  ).to_dataset_dict().popitem()[1].chunk({'time': -1}).sel(time=ref_period)

                            ds_sim = pcat.search(processing_level='regridded_and_rechunked',
                                                 id=sim_id,
                                                 domain=region_name
                                                 ).to_dataset_dict().popitem()[1].chunk({'time': -1}).sel(time=ref_period)

                            # properties
                            sim = calculate_properties(ds=ds_sim, pcat=pcat, step='sim', unstack=True)
                            scen = calculate_properties(ds=ds_scen, pcat=pcat, step='scen')

                            #get ref properties calculated earlier in makeref
                            ref = pcat.search(project=ref_project,
                                               processing_level='diag_ref',
                                               domain=region_name).to_dataset_dict().popitem()[1]

                            save_diagnotics(ref, sim, scen, pcat)

                            if workdir.exists() and workdir.is_dir() and CONFIG["tasks"][-2] == 'diagnostics':
                                shutil.rmtree(workdir)
                                os.mkdir(workdir)
                            if exec_wdir.exists() and exec_wdir.is_dir() and CONFIG["tasks"][-2] == 'diagnostics':
                                shutil.rmtree(exec_wdir)
                                os.mkdir(exec_wdir)
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
                dsC = dsC.chunk({'time':1460, 'lat':50, 'lon':50})
                save_to_zarr(ds=dsC,
                             filename=dsC_path,
                             mode='o')
                pcat.update_from_ds(ds=dsC, info_dict={'domain': 'concat_regions'},
                                    path=str(dsC_path))

                print('All concatenations done for today.')
