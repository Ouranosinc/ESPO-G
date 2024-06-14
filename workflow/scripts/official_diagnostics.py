from dask.distributed import Client
from dask import config as dskconf
import atexit
from pathlib import Path
import xarray as xr
import shutil
import logging
import numpy as np
from dask.diagnostics import ProgressBar
import xscen as xs
import glob
from itertools import product
from xclim.core.calendar import convert_calendar, get_calendar, date_range_like,doy_to_days_since
from xclim.sdba import properties
import xclim as xc
from xscen.xclim_modules import conversions


from xscen.utils import minimum_calendar, translate_time_chunk, stack_drop_nans
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
    clean_up)

from utils import  save_move_update,move_then_delete, save_and_update, large_move

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])


    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)


    # iter over step (ref, sim, scen)
    for step, step_dict in CONFIG['off-diag']['steps'].items():
        if step == "ref":
            dict_input = xr.open_zarr(snakemake.input.ref)
        elif step == "sim":
            dict_input = xr.open_zarr(snakemake.input.sim)
        elif step == "scen":
            dict_input = xr.open_zarr(snakemake.input.scen)

    # iter over datasets in that setp
        for name_input, ds_input in dict_input.items():
            id = ds_input.attrs['cat:id']

            with (
                Client(n_workers=3, threads_per_worker=5,
                       memory_limit="20GB", **daskkws),
                measure_time(name=f'off-diag {snakemake.wildcards.dom_name} {step} {id}',
                             logger=logger),
                timeout(18000, task='off-diag')
            ):

                # unstack
                if step_dict['unstack']:
                    ds_input = xs.utils.unstack_fill_nan(ds_input)

                # cut the domain
                ds_input = xs.spatial.subset(
                    ds_input.chunk({'time': -1}), **CONFIG['off-diag']['domains'][snakemake.wildcards.dom_name])

                dref_for_measure = None
                if 'dref_for_measure' in step_dict:
                    dref_for_measure = pcat.search(
                        domain=dom_name,
                        **step_dict['dref_for_measure']).to_dask()

                if 'dtr' not in ds_input:
                    ds_input = ds_input.assign(dtr=conversions.dtr(ds_input.tasmin, ds_input.tasmax))

                prop, meas = xs.properties_and_measures(
                    ds=ds_input,
                    dref_for_measure=dref_for_measure,
                    to_level_prop=f'off-diag-{step}-prop',
                    to_level_meas=f'off-diag-{step}-meas',
                    **step_dict['properties_and_measures']
                )
                for ds in [prop, meas]:
                    if ds:
                        xs.save_to_zarr(ds, CONFIG['paths']['exec_diag'],
                            itervar=True,
                            rechunk=CONFIG['custom']['rechunk']
                        )
                shutil.rmtree(f'{exec_wdir}/{step}_{id}_{snakemake.wildcards.dom_name}_dtr.zarr',
                              ignore_errors=True)


