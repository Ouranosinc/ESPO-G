import os
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster
import copy

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':
    
    client=dask_cluster(snakemake.params)

    args=copy.deepcopy(CONFIG['extraction']['simulation']['search_data_catalogs'])
    args['other_search_criteria'] = {'id': snakemake.wildcards.sim_id}
    # search cat
    cat_sim_id = xs.search_data_catalogs(**args,)

    # extract
    dc_id = cat_sim_id.popitem()[1]
    ds_sim = xs.extract_dataset(catalog=dc_id,
                                region=CONFIG['custom']['amno_region'],
                                **CONFIG['extraction']['simulation']['extract_dataset'],
                                )['D']

    # clean up time
    ds_sim['time'] = ds_sim.time.dt.floor('D') 

    ds_sim = ds_sim.chunk(CONFIG['extraction']['simulation']['chunks'])
    
    # trick to fix CanESM5
    if 'CMIP6_ScenarioMIP_CCCma_CanESM5_ssp585_r1i1p1f1_global' == snakemake.wildcards.sim_id:
        ds_sim['pr'] = ds_sim['pr'].astype('float32')
        ds_sim['dtr'] = ds_sim['dtr'].astype('float32')
        ds_sim['tasmax'] = ds_sim['tasmax'].astype('float32')
        ds_sim['tasmin'] = ds_sim['tasmin'].astype('float32')
    
    # save to zarr
    xs.save_to_zarr(ds_sim, snakemake.output[0])
