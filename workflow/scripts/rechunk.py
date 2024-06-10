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
    clean_up
)
xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    #atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    cat_sim = xs.search_data_catalogs(
            **CONFIG['extraction']['simulation']['search_data_catalogs'])
    sim_id = list(cat_sim.keys())

    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': sim_id}
    logger.info(fmtkws)


#  ---RECHUNK---
    with (
            Client(n_workers=2, threads_per_worker=5, memory_limit="18GB", **daskkws),
            measure_time(name=f'rechunk', logger=logger),
            timeout(18000, task='rechunk')
    ):
        #rechunk in exec
        rechunk(path_in=snakemake.input[0],
                path_out=snakemake.output[0],
                chunks_over_dim=CONFIG['custom']['chunks'],
                overwrite=True)


        ds_sim_rechunked = xr.open_zarr(snakemake.output[0], decode_timedelta=False)
        xs.save_to_zarr(ds_sim_rechunked, snakemake.output[0])
