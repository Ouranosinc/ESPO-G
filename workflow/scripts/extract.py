
import os
from copy import deepcopy

import xscen as xs
import xclim as xc
from workflow.scripts.utils import dask_cluster
import copy
import numpy as np
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    sim_id=snakemake.wildcards.sim_id
    output=snakemake.output
    
    client=dask_cluster(snakemake.params, config['dask']['client'])

    args=deepcopy(config['extraction']['simulation']['search_data_catalogs'])
    args['other_search_criteria'] = {'id': sim_id}
    # search cat
    cat_sim_id = xs.search_data_catalogs(**args,)

    # extract
    dc_id = cat_sim_id.popitem()[1]
    dict_sim = xs.extract_dataset(catalog=dc_id,
                                region=config['full_region'],
                                **config['extraction']['simulation']['extract_dataset'],
                                )

    ds_sim=dict_sim['D']
    # clean up time
    ds_sim['time'] = ds_sim.time.dt.floor('D') 

    if 'mask' not in ds_sim and 'create_mask' in config['extraction']['simulation']:
        ds_sim["mask"] = xs.regrid.create_mask(dict_sim['fx'], **config['extraction']['simulation']['create_mask'])


    ds_sim = xs.clean_up(ds_sim, **config['extraction']['clean_up'])

    # # patch holes
    # ds_sim['tasmax']= ds_sim['tasmax'].chunk({"time": -1}).interpolate_na("time", method="linear")
    # ds_sim['tasmin']= ds_sim['tasmin'].chunk({"time": -1}).interpolate_na("time", method="linear")
    # ds_sim['dtr']= ds_sim['dtr'].chunk({"time": -1}).interpolate_na("time", method="linear")
    # l = ds_sim.sizes["time"]
    # valid = ds_sim['pr'].notnull().sum(dim="time")
    # ds_sim['pr'] = ds_sim['pr'].where(((valid== l) | (valid == 0)), other=0)

    ds_sim = ds_sim.chunk(config['chunks']['pre-regrid'])

    #ds_sim = ds_sim.chunk({'time': -1})
    
    # trick to fix CanESM5
    if 'CMIP6_ScenarioMIP_CCCma_CanESM5_ssp585_r1i1p1f1_global' == sim_id:
        ds_sim['pr'] = ds_sim['pr'].astype('float32')
        ds_sim['dtr'] = ds_sim['dtr'].astype('float32')
        ds_sim['tasmax'] = ds_sim['tasmax'].astype('float32')
        ds_sim['tasmin'] = ds_sim['tasmin'].astype('float32')

    #FIXME: remove when data is fixed
    if "CMIP6_CORDEX_NorESM2-MM_r1i1p1f1_OURANOS_CRCM5-SN_historical_r1_NAM-12" == sim_id:
         ds_sim['tasmin']=ds_sim['tasmin'].where(ds_sim['tasmin']!=0, np.nan)


    # save to zarr
    xs.save_to_zarr(ds_sim, output['extract'], **config['save_to_zarr'])

    # check that input is fine
    #hc = xs.diagnostics.health_checks(
    #ds=ds_sim,
    #**CONFIG['health_checks']['extract'])

    #hc.attrs.update(ds_sim.attrs)

    #tmp_zarr_and_zip(hc, snakemake.output.checks)

    