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
from xscen import CONFIG

def inter_region():
    file_ref = []
    calandar = ["_default.zarr", "_noleap.zarr", "_360_day.zarr"]
    for region_name in CONFIG['custom']['regions'].keys():
        for cal in calandar:
            file_ref.append("ref/ref_"+f"{region_name}_{cal}")
    return file_ref