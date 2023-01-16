from dask.distributed import Client
from dask import config as dskconf
import atexit
from pathlib import Path
import xarray as xr
import shutil
import logging
import numpy as np
from matplotlib import pyplot as plt
import os
from dask.diagnostics import ProgressBar
import dask
import xesmf
import xscen as xs

from xclim.core.calendar import convert_calendar, get_calendar, date_range_like
from xclim.core.units import convert_units_to
from xclim.sdba import properties, measures, construct_moving_yearly_window, unpack_moving_yearly_window
import xclim as xc
from xclim.core import dataflags

from xscen.utils import minimum_calendar, translate_time_chunk, stack_drop_nans, unstack_fill_nan, maybe_unstack
from xscen.io import rechunk
from xscen import (
    ProjectCatalog,
    search_data_catalogs,
    extract_dataset,
    save_to_zarr,
    load_config,
    CONFIG,
    regrid_dataset,
    train, adjust,
    measure_time, send_mail, send_mail_on_exit, timeout, TimeoutException,
    clean_up
)

from utils import  save_move_update,email_nan_count,move_then_delete

# Load configuration
load_config('configuration/paths_ESPO-G.yml', 'configuration/config_ESPO-G.yml', verbose=(__name__ == '__main__'), reset=True)
logger = logging.getLogger('xscen')

workdir = Path(CONFIG['paths']['workdir'])
exec_wdir = Path(CONFIG['paths']['exec_workdir'])
regriddir = Path(CONFIG['paths']['regriddir'])
refdir = Path(CONFIG['paths']['refdir'])

mode = 'o'



if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    atexit.register(send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    # defining variables
    ref_period = slice(*map(str, CONFIG['custom']['ref_period']))
    sim_period = slice(*map(str, CONFIG['custom']['sim_period']))
    ref_source = CONFIG['extraction']['ref_source']

    tdd = CONFIG['tdd']

    # initialize Project Catalog
    if "initialize_pcat" in CONFIG["tasks"]:
        pcat = ProjectCatalog.create(CONFIG['paths']['project_catalog'], project=CONFIG['project'], overwrite=True)

    # load project catalog
    pcat = ProjectCatalog(CONFIG['paths']['project_catalog'])

    # ---MAKEREF---
    for region_name, region_dict in CONFIG['custom']['regions'].items():
        if (
                "makeref" in CONFIG["tasks"]
                and not pcat.exists_in_cat(domain=region_name, processing_level='nancount', source=ref_source)
        ):
            # default
            if not pcat.exists_in_cat(domain=region_name, source=ref_source):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):
                    # search
                    cat_ref = search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

                    # extract
                    dc = cat_ref.popitem()[1]
                    ds_ref = extract_dataset(catalog=dc,
                                             region=region_dict,
                                             **CONFIG['extraction']['reference']['extract_dataset']
                                             )['D']

                    # stack
                    if CONFIG['custom']['stack_drop_nans']:
                        variables = list(CONFIG['extraction']['reference']['search_data_catalogs'][
                                             'variables_and_freqs'].keys())
                        ds_ref = stack_drop_nans(
                            ds_ref,
                            ds_ref[variables[0]].isel(time=130, drop=True).notnull(),
                        )
                    ds_ref = ds_ref.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_ref.dims})

                    save_move_update(ds=ds_ref,
                                     pcat = pcat,
                                     init_path=f"{exec_wdir}/ref_{region_name}_default.zarr",
                                     final_path=f"{refdir}/ref_{region_name}_default.zarr",
                                     info_dict={'calendar': 'default'
                                                })

            # noleap
            if not pcat.exists_in_cat(domain=region_name, calendar='noleap', source=ref_source):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):

                    ds_ref = pcat.search(source=ref_source,calendar='default',domain=region_name).to_dask()

                    # convert calendars
                    ds_refnl = convert_calendar(ds_ref, "noleap")
                    save_move_update(ds=ds_refnl,
                                     pcat=pcat,
                                     init_path=f"{exec_wdir}/ref_{region_name}_noleap.zarr",
                                     final_path=f"{refdir}/ref_{region_name}_noleap.zarr",
                                     info_dict={'calendar': 'noleap'})
            # 360_day
            if not pcat.exists_in_cat(domain=region_name, calendar='360_day', source=ref_source):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)) :

                    ds_ref = pcat.search(source=ref_source,calendar='default',domain=region_name).to_dask()

                    ds_ref360 = convert_calendar(ds_ref, "360_day", align_on="year")
                    save_move_update(ds=ds_ref360,
                                     pcat=pcat,
                                     init_path=f"{exec_wdir}/ref_{region_name}_360_day.zarr",
                                     final_path=f"{refdir}/ref_{region_name}_360_day.zarr",
                                     info_dict={'calendar': '360_day'})

            # nan_count
            if not pcat.exists_in_cat(domain=region_name, processing_level='nancount', source=ref_source):
                with (Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws)):

                    # search
                    cat_ref = search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

                    # extract
                    dc = cat_ref.popitem()[1]
                    ds_ref = extract_dataset(catalog=dc,
                                             region=region_dict,
                                             **CONFIG['extraction']['reference']['extract_dataset']
                                             )['D']

                    # drop to make faster
                    dref_ref = ds_ref.drop_vars('dtr')

                    dref_ref = dref_ref.chunk({'lat': 225, 'lon': 252, 'time': 168})

                    # diagnostics
                    if 'diagnostics' in CONFIG['tasks']:
                        prop, _ = xs.properties_and_measures(
                            ds=dref_ref,
                            **CONFIG['extraction']['reference']['properties_and_measures']
                        )


                        path_diag = Path(CONFIG['paths']['diagnostics'].format(region_name=region_name,
                                                                               sim_id=prop.attrs['cat:id'],
                                                                               level= prop.attrs['cat:processing_level']))
                        path_diag_exec = f"{workdir}/{path_diag.name}"
                        save_move_update(ds=prop,
                                         pcat=pcat,
                                         init_path=path_diag_exec,
                                         final_path=path_diag,
                                         )

                    # nan count
                    ds_ref_props_nan_count = dref_ref.to_array().isnull().sum('time').mean('variable').chunk(
                        {'lon': 10, 'lat': 10})
                    ds_ref_props_nan_count = ds_ref_props_nan_count.to_dataset(name='nan_count')
                    ds_ref_props_nan_count.attrs.update(ds_ref.attrs)

                    save_move_update(ds=ds_ref_props_nan_count,
                                     pcat=pcat,
                                     init_path=f"{exec_wdir}/ref_{region_name}_nancount.zarr",
                                     final_path=f"{refdir}/ref_{region_name}_nancount.zarr",
                                     info_dict={'processing_level': 'nancount'}
                                     )

                    # plot nan_count and email
                    email_nan_count(path=f"{refdir}/ref_{region_name}_nancount.zarr", region_name=region_name)

    # concat diag-ref-prop
    if (
            "makeref" in CONFIG["tasks"]
            and not pcat.exists_in_cat(domain='NAM',
                                       processing_level='diag-ref-prop',
                                       source=ref_source)
    ):
        # concat
        logger.info(f'Contenating diag-ref-prop.')

        list_dsR = []
        for region_name in CONFIG['custom']['regions']:
            dsR = pcat.search(domain=region_name,
                              processing_level='diag-ref-prop').to_dask()

            list_dsR.append(dsR)

        dsC = xr.concat(list_dsR, 'lat')
        dsC.attrs['cat:domain'] = f"NAM"

        dsC_path = CONFIG['paths'][f"concat_output_diag"].format(
            sim_id = dsC.attrs['cat:id'], level='diag-ref-prop')
        dsC.attrs.pop('cat:path')
        for var in dsC.data_vars:
            dsC[var].encoding.pop('chunks')
        dsC = dsC.chunk({'lat': 50, 'lon': 50})

        save_to_zarr(ds=dsC,
                     filename=dsC_path,
                     mode='o')
        pcat.update_from_ds(ds=dsC,
                            path=str(dsC_path))

    cat_sim = search_data_catalogs(
        **CONFIG['extraction']['simulation']['search_data_catalogs'])
                #periods = ['1950','2100'],  # only for CNRM-ESM2-1
    for sim_id, dc_id in cat_sim.items():
    #if False:
            if not pcat.exists_in_cat(domain='NAM', id =sim_id, processing_level='final'):
                for region_name, region_dict in CONFIG['custom']['regions'].items():
                    # depending on the final tasks, check that the final file doesn't already exists
                    final = {'final_zarr': dict(domain=region_name, processing_level='final', id=sim_id),
                             'diagnostics': dict(domain=region_name, processing_level='diag-improved', id=sim_id)}
                    final_task= 'diagnostics' if 'diagnostics' in CONFIG["tasks"] else 'final_zarr'
                    if not pcat.exists_in_cat(**final[final_task]):

                        fmtkws = {'region_name': region_name, 'sim_id': sim_id}


                        logger.info(fmtkws)

                        # reload project catalog
                        pcat = ProjectCatalog(CONFIG['paths']['project_catalog'])
                        # ---EXTRACT---
                        if (
                                "extract" in CONFIG["tasks"]
                                and not pcat.exists_in_cat(domain='NAM', processing_level='extracted', id=sim_id)
                        ):
                            with (
                                    #Client(n_workers=2, threads_per_worker=5, memory_limit="25GB", **daskkws),
                                    Client(n_workers=1, threads_per_worker=5,memory_limit="50GB", **daskkws), # only for CNRM-ESM2-1

                                    measure_time(name='extract', logger=logger),
                                    timeout(18000, task='extract')
                            ):
                                logger.info('Adding config to log file')
                                f1 = open(
                                    CONFIG['logging']['handlers']['file']['filename'],
                                    'a+')
                                f2 = open('configuration/config_ESPO-G.yml', 'r')
                                f1.write(f2.read())
                                f1.close()
                                f2.close()



                                ds_sim = extract_dataset(catalog=dc_id,
                                                         region= CONFIG['custom']['amno_region'],
                                                         **CONFIG['extraction']['simulation']['extract_dataset'],
                                                         )['D']
                                ds_sim['time'] = ds_sim.time.dt.floor('D') # probably this wont be need when data is cleaned

                                # need lat and lon -1 for the regrid
                                ds_sim = ds_sim.chunk(CONFIG['extraction']['simulation']['chunks'])
                                #ds_sim = ds_sim.chunk({'time': 1, 'lat': -1, 'lon': -1})# only for CNRM-ESM2-1

                                # save to zarr
                                path_cut_exec = f"{exec_wdir}/{sim_id}_NAM_extracted.zarr"
                                path_cut = f"{workdir}/{sim_id}_NAM_extracted.zarr"

                                save_move_update(ds=ds_sim,
                                                 pcat=pcat,
                                                 init_path=path_cut_exec,
                                                 final_path=path_cut,
                                                 )
                        # ---REGRID---
                        if (
                                "regrid" in CONFIG["tasks"]
                                and not pcat.exists_in_cat(domain=region_name, processing_level='regridded', id=sim_id)
                        ):
                            with (
                                    #Client(n_workers=5, threads_per_worker=3, memory_limit="10GB", **daskkws),
                                    Client(n_workers=3, threads_per_worker=3, memory_limit="16GB", **daskkws),
                                    measure_time(name='regrid', logger=logger),
                                    timeout(18000, task='regrid')
                            ):

                                ds_input = pcat.search(id=sim_id,
                                                    processing_level='extracted',
                                                    domain='NAM').to_dask()

                                ds_target = pcat.search(**CONFIG['regrid']['target'],
                                                        domain=region_name).to_dask()

                                ds_regrid = regrid_dataset(
                                    ds=ds_input,
                                    ds_grid=ds_target,
                                )

                                # chunk time dim
                                ds_regrid = ds_regrid.chunk(
                                    translate_time_chunk({'time': '4year'},
                                                         get_calendar(ds_regrid),
                                                         ds_regrid.time.size
                                                         )
                                                                    )

                                # save
                                save_move_update(ds=ds_regrid,
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
                                print(f"{workdir}/{sim_id}_{region_name}_regridded.zarr")
                                print(path_rc)
                                rechunk(path_in=f"{workdir}/{sim_id}_{region_name}_regridded.zarr",
                                        path_out=path_rc,
                                        chunks_over_dim=CONFIG['custom']['chunks'],
                                        overwrite=True)
                                # move to workdir
                                shutil.move(f"{exec_wdir}/{sim_id}_{region_name}_regchunked.zarr",f"{workdir}/{sim_id}_{region_name}_regchunked.zarr")

                                ds_sim_rechunked = xr.open_zarr(f"{workdir}/{sim_id}_{region_name}_regchunked.zarr", decode_timedelta=False)
                                pcat.update_from_ds(ds=ds_sim_rechunked,
                                                    path=f"{workdir}/{sim_id}_{region_name}_regchunked.zarr",
                                                    info_dict={'processing_level': 'regridded_and_rechunked'})

                        # ---BIAS ADJUST---
                        for var, conf in CONFIG['biasadjust']['variables'].items():

                            # ---TRAIN ---
                            if (
                                    "train" in CONFIG["tasks"]
                                    and not pcat.exists_in_cat(domain=region_name,id=f'{sim_id}', processing_level =f'training_{var}')
                            ):
                                while True: # if code bugs forever, it will be stopped by the timeout and then tried again
                                    try:
                                        with (
                                                Client(n_workers=9, threads_per_worker=3, memory_limit="7GB", **daskkws),
                                                measure_time(name=f'train {var}', logger=logger),
                                                timeout(18000, task='train')
                                        ):
                                            # load hist ds (simulation)
                                            ds_hist = pcat.search(id=sim_id,
                                                                  domain=region_name,
                                                                  processing_level='regridded_and_rechunked').to_dask()

                                            # load ref ds
                                            # choose right calendar
                                            simcal = get_calendar(ds_hist)
                                            refcal = minimum_calendar(simcal, CONFIG['custom']['maximal_calendar'])
                                            ds_ref = pcat.search(source = ref_source,
                                                                 calendar=refcal,
                                                                 domain=region_name).to_dask()


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


                                            ds_tr = ds_tr.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_tr.dims
                                                                 if d in CONFIG['custom']['chunks'].keys() })
                                            save_move_update(ds=ds_tr,
                                                             pcat=pcat,
                                                             init_path=f"{exec_wdir}/{sim_id}_{region_name}_{var}_training.zarr",
                                                             final_path=f"{workdir}/{sim_id}_{region_name}_{var}_training.zarr")
                                            shutil.rmtree(f"{CONFIG['paths']['exec_workdir']}ds_ref.zarr")
                                            shutil.rmtree(f"{CONFIG['paths']['exec_workdir']}ds_hist.zarr")

                                    except TimeoutException:
                                        pass
                                    else:
                                        break

                            # ---ADJUST---
                            if (
                                    "adjust" in CONFIG["tasks"]
                                    and not pcat.exists_in_cat(domain=region_name, id=sim_id, processing_level='biasadjusted',
                                                               variable=var)
                            ):
                                with (
                                        Client(n_workers=5, threads_per_worker=3, memory_limit="12GB", **daskkws),
                                        measure_time(name=f'adjust {var}', logger=logger),
                                        timeout(18000, task='adjust')
                                ):
                                    # load sim ds
                                    ds_sim = pcat.search(id=sim_id,
                                                         processing_level='regridded_and_rechunked',
                                                         domain=region_name).to_dask()
                                    ds_tr = pcat.search(id=f'{sim_id}', processing_level =f'training_{var}', domain=region_name).to_dask()

                                    # there are some negative dtr in the data (GFDL-ESM4). This puts is back to a very small positive.
                                    ds_sim['dtr'] = xc.sdba.processing.jitter_under_thresh(ds_sim.dtr, "1e-4 K")

                                    # adjust
                                    ds_scen = adjust(dsim=ds_sim,
                                                     dtrain=ds_tr,
                                                     **conf['adjusting_args'])


                                    save_move_update(ds=ds_scen,
                                                     pcat=pcat,
                                                     init_path=f"{exec_wdir}/{sim_id}_{region_name}_{var}_adjusted.zarr",
                                                     final_path=f"{workdir}/{sim_id}_{region_name}_{var}_adjusted.zarr",
                                                     )

                        # ---CLEAN UP ---
                        if (
                                "clean_up" in CONFIG["tasks"]
                                and not pcat.exists_in_cat(domain=region_name, id=sim_id, processing_level='cleaned_up')
                        ):
                            with (
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
                                                     periods=CONFIG['custom']['sim_period']
                                                          )['D']


                                ds = clean_up(ds=ds,
                                              **CONFIG['clean_up']['xscen_clean_up']
                                              )

                                # fix the problematic data
                                if sim_id in CONFIG['clean_up']['problems']:
                                    logger.info('Mask grid cells where tasmin < 100 K.')
                                    ds = ds.where(ds.tasmin > 100)

                                save_move_update(ds=ds,
                                                 pcat=pcat,
                                                 init_path=f"{exec_wdir}/{sim_id}_{region_name}_cleaned_up.zarr",
                                                 final_path = f"{workdir}/{sim_id}_{region_name}_cleaned_up.zarr",
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
                                #rechunk and move to final destination
                                fi_path = Path(f"{CONFIG['paths']['output']}".format(**fmtkws))
                                fi_path.parent.mkdir(exist_ok=True, parents=True)
                                fi_path_exec = f"{exec_wdir}/{fi_path.name}"

                                shutil.copytree(f"{workdir}/{sim_id}_{region_name}_cleaned_up.zarr",
                                            f"{exec_wdir}/{sim_id}_{region_name}_cleaned_up.zarr")

                                #rechunk in exec and move to final path after
                                rechunk(
                                    path_in=f"{exec_wdir}/{sim_id}_{region_name}_cleaned_up.zarr",
                                        path_out=fi_path_exec,
                                        chunks_over_dim=CONFIG['custom']['out_chunks'],
                                        overwrite=True)

                                shutil.move(fi_path_exec, fi_path)

                                # if this is last step, delete workdir, but save log and regridded
                                if CONFIG['custom']['delete_in_final_zarr']:
                                    final_regrid_path = f"{regriddir}/{sim_id}_{region_name}_regchunked.zarr"
                                    path_log = CONFIG['logging']['handlers']['file']['filename']
                                    move_then_delete(dirs_to_delete=[workdir, exec_wdir],
                                                     moving_files=
                                                     [[f"{workdir}/{sim_id}_{region_name}_regchunked.zarr", final_regrid_path],
                                                      [path_log, CONFIG['paths']['logging'].format(**fmtkws)]],
                                                     pcat=pcat)

                                # add final file to catalog
                                ds = xr.open_zarr(fi_path)
                                pcat.update_from_ds(ds=ds, path=str(fi_path), info_dict= {'processing_level': 'final'})

                        # ---DIAGNOSTICS ---
                        if (
                                "diagnostics" in CONFIG["tasks"]
                                and not pcat.exists_in_cat(domain=region_name,
                                                           id=sim_id,
                                                           processing_level='diag-improved')
                        ):
                            with (
                                    Client(n_workers=3, threads_per_worker=5,
                                           memory_limit="20GB", **daskkws),
                                    measure_time(name=f'diagnostics', logger=logger),
                                    timeout(18000, task='diagnostics')
                            ):


                                for step, step_dict in CONFIG['diagnostics'].items():
                                    ds_input = pcat.search(
                                        id=sim_id,
                                        domain=region_name,
                                        **step_dict['input']
                                    ).to_dask().chunk({'time': -1})

                                    dref_for_measure = None
                                    if 'dref_for_measure' in step_dict:
                                        dref_for_measure=pcat.search(
                                            domain=region_name,
                                            **step_dict['dref_for_measure']).to_dask()

                                    prop, meas = xs.properties_and_measures(
                                        ds = ds_input,
                                        dref_for_measure= dref_for_measure,
                                        to_level_prop = f'diag-{step}-prop',
                                        to_level_meas =f'diag-{step}-meas',
                                        **step_dict['properties_and_measures']
                                    )
                                    for ds in [prop, meas]:
                                        path_diag = Path(
                                            CONFIG['paths']['diagnostics'].format(
                                                region_name=region_name,
                                                sim_id=sim_id,
                                                level=ds.attrs['cat:processing_level']))

                                        path_diag_exec = f"{workdir}/{path_diag.name}"
                                        save_to_zarr(ds=ds, filename=path_diag_exec,
                                                     mode='o', itervar=True,
                                                     rechunk={'lat': 50, 'lon': 50})
                                        shutil.move(path_diag_exec, path_diag)
                                        pcat.update_from_ds(ds=ds, path=str(path_diag))


                                meas_datasets= pcat.search(
                                    processing_level = ['diag-sim-meas',
                                                        'diag-scen-meas'],
                                    id = sim_id,
                                    domain=region_name).to_dataset_dict()

                                # make sur sim is first (for improved)
                                order_keys=[f'{sim_id}.{region_name}.diag-sim-meas.fx',
                                            f'{sim_id}.{region_name}.diag-scen-meas.fx']
                                meas_datasets = {k: meas_datasets[k] for k in order_keys}

                                hm = xs.diagnostics.measures_heatmap(meas_datasets)

                                ip = xs.diagnostics.measures_improvement(meas_datasets)

                                for ds in [hm, ip]:
                                    path_diag = Path(
                                        CONFIG['paths']['diagnostics'].format(
                                            region_name=ds.attrs['cat:domain'],
                                            sim_id=ds.attrs['cat:id'],
                                            level=ds.attrs['cat:processing_level']))
                                    save_to_zarr(ds=ds, filename=path_diag, mode='o')
                                    pcat.update_from_ds(ds=ds, path = path_diag)


                                # if this is last step, delete stuff
                                if CONFIG['custom']['delete_in_diag']:
                                    final_regrid_path = f"{regriddir}/{sim_id}_{region_name}_regchunked.zarr"
                                    path_log = \
                                    CONFIG['logging']['handlers']['file'][
                                        'filename']
                                    move_then_delete(
                                        dirs_to_delete=[workdir, exec_wdir],
                                        moving_files=
                                        [[
                                             f"{workdir}/{sim_id}_{region_name}_regchunked.zarr",
                                             final_regrid_path],
                                         [path_log,
                                          CONFIG['paths']['logging'].format(
                                              **fmtkws)]],
                                        pcat=pcat)

                                send_mail(
                                    subject=f"{sim_id}/{region_name} - Succès",
                                    msg=f"Toutes les étapes demandées pour la simulation {sim_id}/{region_name} ont été accomplies.",
                                )

                if (
                        "concat" in CONFIG["tasks"]
                        and not pcat.exists_in_cat(domain='NAM',
                                                   id=sim_id,
                                                   processing_level='final',
                                                   format='zarr')
                ):
                    dskconf.set(num_workers=12)
                    ProgressBar().register()
                    levels = ['diag-sim-prop', 'diag-scen-prop', 'diag-sim-meas', 'diag-scen-meas', 'final']
                    for level in levels:
                        logger.info(f'Contenating {sim_id} {level}.')

                        list_dsR = []
                        for region_name in CONFIG['custom']['regions']:
                            dsR = pcat.search(id=sim_id,
                                              domain=region_name,
                                              processing_level=level).to_dask()

                            list_dsR.append(dsR)

                        dsC = xr.concat(list_dsR, 'lat')

                        dsC.attrs['title'] = f"ESPO-G6 v1.0.0 - {sim_id}"
                        dsC.attrs['cat:domain'] = f"NAM"
                        dsC.attrs.pop('intake_esm_dataset_key')

                        dsC_path = CONFIG['paths'][f"concat_output" \
                                                   f"_{level.split('-')[0]}"].format(
                            sim_id=sim_id, level=level)

                        dsC.attrs.pop('cat:path')
                        if level !='final':
                            dsC = dsC.chunk({ 'lat': 50, 'lon': 50})
                        elif get_calendar(dsC.time) =='360_day':
                            dsC = dsC.chunk({'time':1440, 'lat':50, 'lon':50})
                        else:
                            dsC = dsC.chunk({'time':1460, 'lat':50, 'lon':50})
                        save_to_zarr(ds=dsC,
                                     filename=dsC_path,
                                     mode='o')
                        pcat.update_from_ds(ds=dsC,
                                            path=str(dsC_path))

                    logger.info('All concatenations done.')



    # ---OFFICIAL-DIAGNOSTICS---
    if "official-diag" in CONFIG["tasks"]:
        # iter over small domain
        for dom_name, dom_dict in CONFIG['off-diag']['domains'].items():
            # iter over step (ref, sim, scen)
            for step, step_dict in CONFIG['off-diag']['steps'].items():
                dict_input = pcat.search(domain=step_dict['domain'][dom_name],
                                         **step_dict['input'], ).to_dataset_dict()
                # iter over datasets in that setp
                for name_input, ds_input in dict_input.items():
                    id = ds_input.attrs['cat:id']
                    if not pcat.exists_in_cat(id=id,
                                              processing_level=f'off-diag-{step}-prop',
                                              domain=dom_name):
                        with (
                                Client(n_workers=3, threads_per_worker=5,
                                       memory_limit="20GB", **daskkws),
                                measure_time(name=f'off-diag {dom_name} {step} {id}',
                                             logger=logger),
                                timeout(18000, task='off-diag')
                        ):

                            # unstack
                            if step_dict['unstack']:
                                ds_input = xs.utils.unstack_fill_nan(ds_input)

                            # cut the domain
                            ds_input = xs.extract.clisops_subset(
                                ds_input.chunk({'time': -1}), dom_dict)
                            ds_input.attrs["cat:domain"] = dom_name

                            # correlogram
                            if not pcat.exists_in_cat(id=id,
                                                      processing_level=f'correlogram-{step}',
                                                      domain=dom_name):
                                logging.info(f'Computing correlogram {step}')
                                correlogram = xr.Dataset(attrs=ds_input.attrs)
                                for var in ds_input.data_vars:
                                    correlogram[
                                        f'correlogram_{var}'] = xc.sdba.properties.spatial_correlogram(
                                        ds_input[var],
                                        bins=99
                                    )
                                correlogram.attrs[
                                    "cat:processing_level"] = f'correlogram-{step}'
                                path_diag = Path(
                                    CONFIG['paths']['diagnostics'].format(
                                        region_name=dom_name,
                                        sim_id=id,
                                        level=correlogram.attrs[
                                            'cat:processing_level']))
                                path_diag_exec = f"{exec_wdir}/{path_diag.name}"
                                save_move_update(
                                    ds=correlogram,
                                    pcat=pcat,
                                    init_path=path_diag_exec,
                                    final_path=path_diag,
                                    itervar=True,
                                    rechunk={'lat': 50, 'lon': 50}
                                )

                            dref_for_measure = None
                            if 'dref_for_measure' in step_dict:
                                dref_for_measure = pcat.search(
                                    domain=dom_name,
                                    **step_dict['dref_for_measure']).to_dask()

                            prop, meas = xs.properties_and_measures(
                                ds=ds_input,
                                dref_for_measure=dref_for_measure,
                                to_level_prop=f'off-diag-{step}-prop',
                                to_level_meas=f'off-diag-{step}-meas',
                                **step_dict['properties_and_measures']
                            )
                            for ds in [prop, meas]:
                                if ds:
                                    path_diag = Path(
                                        CONFIG['paths']['diagnostics'].format(
                                            region_name=dom_name,
                                            sim_id=id,
                                            level=ds.attrs['cat:processing_level']))
                                    path_diag_exec = f"{exec_wdir}/{path_diag.name}"

                                    save_move_update(
                                        ds=ds,
                                        pcat=pcat,
                                        init_path=path_diag_exec,
                                        final_path=path_diag,
                                        itervar=True,
                                        rechunk={'lat': 50, 'lon': 50}
                                    )

            # iter over all sim meas
            meas_dict = pcat.search(
                processing_level='off-diag-sim-meas',
                domain=dom_name
            ).to_dataset_dict()
            for id_meas, ds_meas_sim in meas_dict.items():
                sim_id = ds_meas_sim.attrs['cat:id']
                if not pcat.exists_in_cat(id=sim_id,
                                          processing_level='off-diag-improved'):
                    with (
                            Client(n_workers=3, threads_per_worker=5,
                                   memory_limit="20GB", **daskkws),
                            measure_time(name=f'off-diag-meas {dom_name} {sim_id}',
                                         logger=logger),
                    ):
                        # get scen meas
                        meas_datasets = {}
                        meas_datasets[
                            f'{sim_id}.{dom_name}.diag-sim-meas'] = ds_meas_sim
                        meas_datasets[
                            f'{sim_id}.{dom_name}.diag-scen-meas'] = pcat.search(
                            processing_level='off-diag-scen-meas',
                            id=sim_id,
                            domain=dom_name).to_dask()

                        hm = xs.diagnostics.measures_heatmap(meas_datasets)

                        ip = xs.diagnostics.measures_improvement(meas_datasets)

                        # save and update
                        for ds in [hm, ip]:
                            path_diag = Path(
                                CONFIG['paths']['diagnostics'].format(
                                    region_name=ds.attrs['cat:domain'],
                                    sim_id=ds.attrs['cat:id'],
                                    level=ds.attrs['cat:processing_level']))
                            save_to_zarr(ds=ds, filename=path_diag, mode='o')
                            pcat.update_from_ds(ds=ds, path=path_diag)

                        move_then_delete(dirs_to_delete=[workdir, exec_wdir],
                                         moving_files=[], pcat=pcat)



    # ---INDICATORS---
    if "indicators" in CONFIG["tasks"]:
        dict_input = pcat.search(**CONFIG['indicators']['input']).to_dataset_dict()
        for id_input, ds_input in dict_input.items():
            sim_id = ds_input.attrs['cat:id']
            if not pcat.exists_in_cat(id = sim_id, processing_level = 'indicators', xrfreq='AS-JUL' ):


                ds_input = ds_input.assign(tas=xc.atmos.tg(ds=ds_input))
                mod = xs.indicators.load_xclim_module(**CONFIG['indicator']['load_xclim_module'])

                for indname, ind in mod.iter_indicators():
                    var_name = ind.cf_attrs[0]['var_name']
                    freq = ind.injected_parameters['freq'].replace('YS', 'AS-JAN')
                    if not pcat.exists_in_cat(id=sim_id,
                                              processing_level='individual_indicator',
                                              variable=var_name,
                                              xrfreq = freq):
                        with (
                                Client(n_workers=2, threads_per_worker=4,
                                       memory_limit="30GB", **daskkws),
                                measure_time(name=f'indicators {sim_id}',
                                             logger=logger),
                                timeout(10000, indname)
                        ):
                            if freq == '2QS-OCT':
                                iAPR = np.where(ds_input.time.dt.month == 4)[0][0]
                                dsi = ds_input.isel(time=slice(iAPR, None))
                            else:
                                dsi = ds_input
                            if 'rolling' in ind.keywords or freq=='QS-DEC':
                                temppath = f"{exec_wdir}/{sim_id}_{indname}.zarr"
                                mult, *parts = xc.core.calendar.parse_offset(freq)
                                steps = xc.core.calendar.construct_offset(mult * 8, *parts)
                                for i, slc in enumerate(dsi.resample(time=steps).groups.values()):
                                    dsc = dsi.isel(time=slc)
                                    logger.info(f"Computing on slice {dsc.indexes['time'][0]}-{dsc.indexes['time'][-1]}.")
                                    _, out = xs.compute_indicators(
                                        dsc,
                                        indicators=[ind]).popitem()
                                    kwargs = {} if i == 0 else {'append_dim': 'time'}
                                    save_to_zarr(out,
                                                 temppath,
                                                 rechunk={'time': -1},
                                                 mode='a',
                                                 zarr_kwargs=kwargs)

                                logger.info(f'Moving from temp dir to final dir, removing temp dir.')
                                #outpath = f"{workdir}/{sim_id}_{indname}.zarr"
                                #outpath = f"{workdir}/{sim_id}_{indname}.zarr"
                                #shutil.move(exec_wdir, outpath)
                                pcat.update_from_ds(ds=out,
                                                    path=temppath)
                            else:
                                _, out = xs.compute_indicators(
                                    dsi,
                                    indicators=[ind]).popitem()
                                xs.save_to_zarr(out,
                                                f"{exec_wdir}/{sim_id}_{indname}.zarr",
                                                rechunk={'time': -1},
                                                mode='o' )
                                pcat.update_from_ds(out,f"{exec_wdir}/{sim_id}_{indname}.zarr" )


                #iterate over possible freqs
                freqs = pcat.search(processing_level='individual_indicator',
                                    id=sim_id).df.xrfreq.unique()
                for xrfreq in freqs:
                    if not pcat.exists_in_cat(id=sim_id,
                                           processing_level='indicators',
                                           xrfreq=xrfreq):
                        # merge all indicators of this freq in one dataset
                        logger.info(f"Merge {xrfreq} indicators.")
                        with ProgressBar():
                            all_ind = pcat.search(processing_level='individual_indicator',
                                                  id=sim_id,
                                                  xrfreq=xrfreq).to_dataset_dict(**tdd)
                            ds_merge = xr.merge(all_ind.values(),
                                                combine_attrs='drop_conflicts')
                            ds_merge.attrs['cat:processing_level'] = 'indicators'

                            save_move_update(
                                ds=ds_merge,
                                pcat=pcat,
                                init_path=f"{exec_wdir}/{sim_id}_{xrfreq}_indicators.zarr",
                                #init_path=f"{workdir}/{sim_id}_{xrfreq}_indicators.zarr",
                                final_path=Path(CONFIG['paths']['indicators'].format(
                                    **xs.utils.get_cat_attrs(ds_merge)))
                            )

                move_then_delete(dirs_to_delete=[workdir, exec_wdir],moving_files=[],pcat=pcat)

    # --- CLIMATOLOGICAL MEAN ---
    if "climatological_mean" in CONFIG["tasks"]:
        ind_dict = pcat.search( **CONFIG['aggregate']['input']['clim']).to_dataset_dict(**tdd)
        for id_input, ds_input in ind_dict.items():
            xrfreq_input = ds_input.attrs['cat:xrfreq']
            sim_id = ds_input.attrs['cat:id']
            if not pcat.exists_in_cat(id=sim_id, processing_level= 'climatology',
                                  xrfreq=xrfreq_input):
                with (
                        Client(n_workers=5, threads_per_worker=4,memory_limit="6GB", **daskkws),
                        measure_time(name=f'clim {id_input}',logger=logger),
                ):
                    ds_mean = xs.climatological_mean(ds=ds_input)

                    save_move_update(
                        ds=ds_mean,
                        pcat=pcat,
                        itervar=True, #if xrfreq_input=='QS-DEC' else False,
                        rechunk={'time': 4, "lat":50, "lon":50},
                        init_path=f"{exec_wdir}/{sim_id}_{xrfreq_input}_climatology.zarr",
                        final_path=Path(CONFIG['paths']['climatology'].format(
                            **xs.utils.get_cat_attrs(ds_mean)))
                    )

    # --- DELTAS ---
    if "abs-delta" in CONFIG["tasks"]:
        with (
                Client(n_workers=6, threads_per_worker=4, memory_limit="4GB",
                       **daskkws),
                measure_time(name=f'delta', logger=logger),
        ):
            ind_dict = pcat.search( **CONFIG['aggregate']['input']['abs-delta']).to_dataset_dict(**tdd)
            for id_input, ds_input in ind_dict.items():
                xrfreq_input = ds_input.attrs['cat:xrfreq']
                sim_id = ds_input.attrs['cat:id']
                if not pcat.exists_in_cat(id=sim_id, processing_level= 'abs-delta',
                                      xrfreq=xrfreq_input):
                     with (
                    #         Client(n_workers=4, threads_per_worker=4,memory_limit="6GB", **daskkws),
                             measure_time(name=f'delta {id_input}',logger=logger),
                     ):
                        ds_delta = xs.aggregate.compute_deltas(ds=ds_input,
                                                               kind="+",
                                                               to_level='abs-delta')

                        path=Path(CONFIG['paths']['delta'].format(**xs.utils.get_cat_attrs(ds_delta)))
                        xs.save_to_zarr(ds_delta, path)
                        pcat.update_from_ds(ds_delta, path)

                        # save_move_update(
                        #     ds=ds_delta,
                        #     pcat=pcat,
                        #     rechunk={'time': 4, "lat":50, "lon":50},
                        #     init_path=f"{exec_wdir}/{sim_id}_{xrfreq_input}_absdeltas.zarr",
                        #     final_path=Path(CONFIG['paths']['delta'].format(
                        #         **xs.utils.get_cat_attrs(ds_delta)))
                        # )

    # --- DELTAS ---
    if "per-delta" in CONFIG["tasks"]:
        ind_dict = pcat.search( **CONFIG['aggregate']['input']['per-delta']).to_dataset_dict(**tdd)
        for id_input, ds_input in ind_dict.items():
            xrfreq_input = ds_input.attrs['cat:xrfreq']
            sim_id = ds_input.attrs['cat:id']
            if not pcat.exists_in_cat(id=sim_id, processing_level= 'per-delta',
                                  xrfreq=xrfreq_input):
                with (
                        Client(n_workers=4, threads_per_worker=4,memory_limit="6GB", **daskkws),
                        measure_time(name=f'delta {id_input}',logger=logger),
                ):
                    ds_delta = xs.aggregate.compute_deltas(ds=ds_input,
                                                           kind="%",
                                                           to_level='per-delta'
                                                           )

                    path = CONFIG['paths']['delta'].format(**xs.utils.get_cat_attrs(ds_delta))
                    xs.save_to_zarr(ds_delta, path)
                    pcat.update_from_ds(ds_delta, path)

                    # save_move_update(
                    #     ds=ds_delta,
                    #     pcat=pcat,
                    #     rechunk={'time': 4, "lat":50, "lon":50},
                    #     init_path=f"{exec_wdir}/{sim_id}_{xrfreq_input}_perdeltas.zarr",
                    #     final_path=Path(CONFIG['paths']['delta'].format(
                    #         **xs.utils.get_cat_attrs(ds_delta)))
                    # )

    # # --- DELTAS ---
    # if "deltas" in CONFIG["tasks"]:
    #     ind_dict = pcat.search( **CONFIG['aggregate']['input']).to_dataset_dict(**tdd)
    #     for id_input, ds_input in ind_dict.items():
    #         xrfreq_input = ds_input.attrs['cat:xrfreq']
    #         sim_id = ds_input.attrs['cat:id']
    #         if not pcat.exists_in_cat(id=sim_id, processing_level= 'delta_climatology',
    #                               xrfreq=xrfreq_input):
    #             with (
    #                     Client(n_workers=4, threads_per_worker=4,memory_limit="6GB", **daskkws),
    #                     measure_time(name=f'delta {id_input}',logger=logger),
    #             ):
    #                 # cut only canada for comparison with PCIC
    #                 ds_input = ds_input.sel(lat=slice(41, 84), lon =slice(-141, -52))
    #                 ds_mean = xs.climatological_mean(ds=ds_input)
    #                 ds_delta = xs.aggregate.compute_deltas(ds=ds_mean)
    #
    #                 save_move_update(
    #                     ds=ds_delta,
    #                     pcat=pcat,
    #                     rechunk={'time': 4, "lat":50, "lon":50},
    #                     init_path=f"{exec_wdir}/{sim_id}_{xrfreq_input}_deltas.zarr",
    #                     final_path=Path(CONFIG['paths']['deltas'].format(
    #                         **xs.utils.get_cat_attrs(ds_delta)))
    #                 )


    if "ensemble" in CONFIG["tasks"]:
        # one ensemble (file) per level, per xrfreq, per variable, per experiment
        for processing_level in CONFIG['ensemble']['processing_levels']:
            ind_df = pcat.search(processing_level=processing_level).df
            # iterate through available xrfreq, exp and variables
            for experiment in ind_df.experiment.unique():
                for xrfreq in ind_df.xrfreq.unique():
                    for variable in list(ind_df[ind_df['xrfreq']==xrfreq].variable.unique()[0]):

                        ind_dict = pcat.search( processing_level=processing_level,
                                                experiment=experiment,
                                                xrfreq=xrfreq,
                                                variable=variable).to_dataset_dict(**tdd)

                        if not pcat.exists_in_cat(
                                processing_level= f'ensemble-{processing_level}',
                                xrfreq=xrfreq,
                                experiment=experiment,
                                variable=variable
                        ):
                            with (
                                    #Client(n_workers=3, threads_per_worker=4,memory_limit="15GB", **daskkws),
                                    ProgressBar(),
                                    measure_time(name=f'ensemble-{processing_level}',logger=logger),
                            ):
                                ens = xs.ensembles.ensemble_stats(
                                    datasets=ind_dict,
                                    to_level= f'ensemble-{processing_level}',
                                    **CONFIG['ensemble']['ensemble_stats_xscen']
                                )

                                ens.attrs['cat:variable']= xs.catalog.parse_from_ds(ens, ["variable"])["variable"]

                                # path = Path(CONFIG['paths']['ensemble'].format(var=variable,
                                #     **xs.utils.get_cat_attrs(ens)))
                                # xs.save_to_zarr(ens, path)
                                # pcat.update_from_ds(ens, path)

                                save_move_update(
                                    ds=ens,
                                    pcat=pcat,
                                    #rechunk={'time': 4, "lat":50, "lon":50},
                                    init_path=f"{exec_wdir}/ensemble_{processing_level}_{variable}_{xrfreq}_{experiment}.zarr",
                                    final_path=Path(CONFIG['paths']['ensemble'].format(
                                        var =variable, **xs.utils.get_cat_attrs(ens)))
                                )

