
import os
from copy import deepcopy
import xarray as xr
import xscen as xs
import xclim as xc
from workflow.scripts.utils import dask_cluster, save
import copy
import numpy as np
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs=snakemake.input
    output=snakemake.output[0]
    
    client=dask_cluster(snakemake.params,config['dask']['client'])


    ds_sim = xr.open_zarr(inputs[0], decode_timedelta=False)
    ds_sim=ds_sim.chunk({"time": -1})
    # patch holes
    ds_sim['tasmax']= ds_sim['tasmax'].interpolate_na("time", method="linear")
    # ds_sim['tasmin']= ds_sim['tasmin'].interpolate_na("time", method="linear")
    # ds_sim['dtr']= ds_sim['dtr'].interpolate_na("time", method="linear")
    # #l = ds_sim.sizes["time"]
    # #valid = ds_sim['pr'].notnull().sum(dim="time")
    # #ds_sim['pr'] = ds_sim['pr'].where(((valid== l) | (valid == 0)), other=0)
    # ds_sim['pr'] = ds_sim['pr'].where(ds_sim['pr'].notnull(), other=0)

    ds_sim = ds_sim.chunk(config['chunks']['pre-regrid'])
    
    
    # save to zarr
    save(ds_sim,output, itervar=True)

    # check that input is fine
    #hc = xs.diagnostics.health_checks(
    #ds=ds_sim,
    #**CONFIG['health_checks']['extract'])

    #hc.attrs.update(ds_sim.attrs)

    #tmp_zarr_and_zip(hc, snakemake.output.checks)

    