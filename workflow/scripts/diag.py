import os
import copy
import xarray as xr
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml","config/config_region.yml","config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    # load data that we already have
    ref_prop=xr.open_zarr(snakemake.input.ref_prop,decode_timedelta=False)

    ds_scen=xr.open_mfdataset([snakemake.input[f'scen_{v}'] for v 
                               in CONFIG['diagnostics']['properties_and_measures']['change_units_arg'].keys()],
                               engine='zarr',
                               decode_timedelta=False)
    ds_scen = xs.spatial.subset(ds_scen, **CONFIG['diagregion'][snakemake.wildcards.dregion])



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
    # need lat and lon -1 for the regrid
    ds_sim = ds_sim.chunk(CONFIG['chunks']['pre-regrid'])
    if 'hursmin' in ds_sim:
        ds_sim = ds_sim.rename({'hursmin': 'hursTasmax'})


    # get target ref grid
    ds_target = xr.open_zarr(snakemake.input.ref, decode_timedelta=False)
    ds_target = xs.spatial.subset(ds_target, **CONFIG['diagregion'][snakemake.wildcards.dregion])

    # regrid
    args=CONFIG['regrid']['regrid_dataset'].copy()
    args['regridder_kwargs']['locstream_out']=False
    ds_sim = xs.regrid_dataset(
        ds=ds_sim,
        ds_grid=ds_target,
        weights_location= f"{os.environ['SLURM_TMPDIR']}/weights/",
        **args
    )
    #mask nan
    mask=ds_target['tasmax'].isel(time=130, drop=True).notnull().compute()
    ds_sim=ds_sim.where(mask)

    # chunk
    ds_sim = ds_sim.chunk({d: CONFIG['chunks']['working'][d] for d in ds_sim.dims})
    ds_scen = ds_scen.chunk({d: CONFIG['chunks']['working'][d] for d in ds_scen.dims})

    sim_prop, sim_meas = xs.properties_and_measures(
                                ds=ds_sim,
                                dref_for_measure=ref_prop,
                                **CONFIG['diagnostics']['properties_and_measures']
                            )
    
    scen_prop, scen_meas = xs.properties_and_measures(
                            ds=ds_scen,
                            dref_for_measure=ref_prop,
                            **CONFIG['diagnostics']['properties_and_measures']
                        )
    for out, name in zip([sim_prop, sim_meas, scen_prop, scen_meas],['sim_prop','sim_meas','scen_prop','scen_meas']):
        out = out.chunk(CONFIG['chunks']['diag'])
        tmp_zarr_and_zip(out, snakemake.output[name])

    imp = xs.diagnostics.measures_improvement([sim_meas,scen_meas])
    tmp_zarr_and_zip(imp, snakemake.output.imp)


