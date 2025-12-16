import os
import xscen as xs
from xscen import CONFIG
import xclim as xc
import xarray as xr

from workflow.scripts.utils import dask_cluster
import copy
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

if __name__ == '__main__':
    
    client=dask_cluster(snakemake.params)


    sim_id=snakemake.wildcards.sim_id
    args=copy.deepcopy(CONFIG['extraction']['simulation']['search_data_catalogs'])
    args['other_search_criteria'] = {'id': sim_id}
    
    #FIXME: remove when fix https://github.com/Ouranosinc/xscen/issues/669
    if 'ssp534-over' in sim_id:
        args['periods'][0]='2040'


    # search cat
    cat_sim_id = xs.search_data_catalogs(**args,)

    # extract
    dc_id = cat_sim_id.popitem()[1]


    #FIXME: trick to fix time until xscen13.1, PR661
    def pre(ds):
        if 'time' in ds:
            ds['time']= ds.time.dt.floor('D')
        return ds
    ds_sim = xs.extract_dataset(catalog=dc_id,
                                region=CONFIG['custom']['full_region'],
                                preprocess=pre, # FIXME: see above
                                **CONFIG['extraction']['simulation']['extract_dataset'],
                                )['D']

    #FIXME: remove when fix https://github.com/Ouranosinc/xscen/issues/669
    if 'ssp534-over' in sim_id:
        
        args=copy.deepcopy(CONFIG['extraction']['simulation']['search_data_catalogs'])
        args['other_search_criteria'] = {'id': 
                                        sim_id.replace('ssp534-over', 'ssp585')}
        args['periods'][1]='2039'
        # search cat
        cat_sim_id = xs.search_data_catalogs(**args,)

        # extract
        dc_id = cat_sim_id.popitem()[1]

        ds_filler = xs.extract_dataset(catalog=dc_id,
                                    region=CONFIG['custom']['full_region'],
                                    preprocess=pre, # FIXME: see above
                                    **CONFIG['extraction']['simulation']['extract_dataset'],
                                    )['D']
        
        #  put on the same time axis                                                                        
        ds1, ds2 = xr.align(ds_sim, ds_filler, join="outer")
        # fill the hole
        ds_sim = ds1.combine_first(ds2)


    # clean up time
    ds_sim['time'] = ds_sim.time.dt.floor('D') 

    ds_sim = xs.clean_up(ds_sim, **CONFIG['extraction']['clean_up'])

    ds_sim = ds_sim.chunk(CONFIG['chunks']['pre-regrid'])
    
    # trick to fix CanESM5
    if 'CMIP6_ScenarioMIP_CCCma_CanESM5_ssp585_r1i1p1f1_global' == snakemake.wildcards.sim_id:
        ds_sim['pr'] = ds_sim['pr'].astype('float32')
        ds_sim['dtr'] = ds_sim['dtr'].astype('float32')
        ds_sim['tasmax'] = ds_sim['tasmax'].astype('float32')
        ds_sim['tasmin'] = ds_sim['tasmin'].astype('float32')
    
    # save to zarr
    xs.save_to_zarr(ds_sim, snakemake.output[0])
