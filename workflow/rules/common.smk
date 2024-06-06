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
ProjectCatalog,search_data_catalogs,extract_dataset,save_to_zarr,load_config,CONFIG,regrid_dataset,
train, adjust,measure_time, send_mail, send_mail_on_exit, timeout, TimeoutException,clean_up)
import snakemake

from snakemake.utils import validate

exec_wdir = Path(config['paths']['exec_workdir'])
regriddir = Path(config['paths']['regriddir'])
refdir = Path(config['paths']['refdir'])

ref_period = slice(*map(str,config['custom']['ref_period']))
sim_period = slice(*map(str,config['custom']['sim_period']))
ref_source = config['extraction']['ref_source']

pcat = xs.ProjectCatalog(config['paths']['project_catalog'], create=True)
def inter_region():
    file_ref = []
    calandar = ["_default.zarr", "_noleap.zarr", "_360_day.zarr"]
    for region_name in config['custom']['regions'].keys():
        for cal in calandar:
            file_ref.append(Path(config['paths']['refdir'])/f"ref_{region_name}{cal}")
    return file_ref

