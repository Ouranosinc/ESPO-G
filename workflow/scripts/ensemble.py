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

    fmtkws = {'xrfreq': snakemake.wildcards.xrfreq, 'sim_id': snakemake.wildcards.sim_id, 'region':  snakemake.wildcards.region}
    logger.info(fmtkws)


    # one ensemble (file) per level, per xrfreq, per variable, per experiment
    domain= CONFIG['ensemble']['domain']
    for processing_level in CONFIG['ensemble']['processing_levels']:
        ind_df = pcat.search(processing_level=processing_level,domain= domain).df
        # iterate through available xrfreq, exp and variables
        for experiment, xrfreq in product(ind_df.experiment.unique(), ind_df.xrfreq.unique()):
            for variable in list(ind_df[ind_df['xrfreq']==xrfreq].variable.unique()[0]):

                ind_dict = pcat.search( processing_level=processing_level,
                                        experiment=experiment,
                                        xrfreq=xrfreq,
                                        domain= domain,
                                        source=CONFIG['ensemble']['source'],
                                        variable=variable).to_dataset_dict(**tdd)

                if not pcat.exists_in_cat(
                        processing_level= f'ensemble-{processing_level}',
                        xrfreq=xrfreq,
                        experiment=experiment,
                        domain=domain,
                        variable=variable+ "_p50",
                ) and len(ind_dict)==14:
                    with (
                            ProgressBar(),
                            xs.measure_time(name=f'ensemble- {domain} {experiment}'
                                              f' {processing_level}  {xrfreq} {variable}',logger=logger),
                    ):
                        ens = xs.ensembles.ensemble_stats(
                            datasets=ind_dict,
                            to_level= f'ensemble-{processing_level}',
                            **CONFIG['ensemble']['ensemble_stats_xscen']
                        )

                        ens.attrs['cat:variable']= xs.catalog.parse_from_ds(ens, ["variable"])["variable"]
                        ens.attrs['cat:var'] = variable # for final filename

                        xs.save_to_zarr(ens, f"{exec_wdir}/{domain}_{processing_level}_{variable}_{xrfreq}_{experiment}_ensemble.zarr",
                        )

    # large_move(exec_wdir, "ensemble", CONFIG['paths']['ensemble'], pcat)