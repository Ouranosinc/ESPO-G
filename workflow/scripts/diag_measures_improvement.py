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


    fmtkws = {'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)


# iter over all sim meas
meas_dict = pcat.search(
    processing_level='off-diag-sim-meas',
    domain=dom_name
).to_dataset_dict()
for id_meas, ds_meas_sim in meas_dict.items():
    sim_id = ds_meas_sim.attrs['cat:id']

    with (
        Client(n_workers=3, threads_per_worker=5,
               memory_limit="20GB", **daskkws),
        measure_time(name=f'off-diag-meas {snakemake.wildcards.dom_name} {sim_id}',
                     logger=logger),
    ):
        # get scen meas
        meas_datasets = {}
        meas_datasets[f'{sim_id}.{snakemake.wildcards.dom_name}.diag-sim-meas'] = ds_meas_sim
        meas_datasets[f'{sim_id}.{snakemake.wildcards.dom_name}.diag-scen-meas'] = pcat.search(
            processing_level='off-diag-scen-meas',
            id=sim_id,
            domain=snakemake.wildcards.dom_name
        ).to_dask()

        ip = xs.diagnostics.measures_improvement(meas_datasets)

        # save and update

        save_and_update(ds=ip, pcat=pcat,
                        path=CONFIG['paths']['exec_diag'])

# move to final destination
large_move(exec_wdir, "", CONFIG['paths']['final_diag'], pcat)