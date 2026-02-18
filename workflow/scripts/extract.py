
import os
from copy import deepcopy
import cftime

import xscen as xs
import xclim as xc
from workflow.scripts.utils import dask_cluster
import copy
from datetime import datetime
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

    ds_sim = ds_sim.chunk(config['chunks']['pre-regrid'])

    
    # trick to fix CanESM5
    if 'CMIP6_ScenarioMIP_CCCma_CanESM5_ssp585_r1i1p1f1_global' == sim_id:
        ds_sim['pr'] = ds_sim['pr'].astype('float32')
        ds_sim['dtr'] = ds_sim['dtr'].astype('float32')
        ds_sim['tasmax'] = ds_sim['tasmax'].astype('float32')
        ds_sim['tasmin'] = ds_sim['tasmin'].astype('float32')


    # save to zarr
    xs.save_to_zarr(ds_sim, output['extract'], **config['save_to_zarr'])

    