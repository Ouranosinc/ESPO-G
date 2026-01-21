from copy import deepcopy
import os
import copy
import xarray as xr
import xscen as xs
from workflow.scripts.utils import dask_cluster, save
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs=snakemake.input
    dregion=snakemake.wildcards.dregion
    sim_id=snakemake.wildcards.sim_id
    output=snakemake.output

    client=dask_cluster(snakemake.params, config['dask']['client'])

    # load data that we already have
    ref_prop=xr.open_zarr(inputs['ref_prop'],decode_timedelta=False)

    ds_scen=xr.open_mfdataset([inputs[f'scen_{v}'] for v 
                               in config['diagnostics']['properties_and_measures']['change_units_arg'].keys()],
                               engine='zarr',
                               decode_timedelta=False)
    ds_scen = xs.spatial.subset(ds_scen, **config['diagregion'][dregion])



    # Create ds_sim for full region
    args=copy.deepcopy(config['extraction']['simulation']['search_data_catalogs'])
    args['other_search_criteria'] = {'id': sim_id}
    cat_sim_id = xs.search_data_catalogs(**args,)
    dc_id = cat_sim_id.popitem()[1]
    region_dict=config['custom']['full_region']
    ds_sim = xs.extract_dataset(catalog=dc_id,
                                region=region_dict,
                                **config['extraction']['simulation']['extract_dataset'],
                                )['D']
    ds_sim['time'] = ds_sim.time.dt.floor('D') # probably this wont be need when data is cleaned
    # need lat and lon -1 for the regrid
    ds_sim = ds_sim.chunk(config['chunks']['pre-regrid'])
    if 'hursmin' in ds_sim:
        ds_sim = ds_sim.rename({'hursmin': 'hursTasmax'})


    # get target ref grid
    ds_target = xr.open_zarr(inputs['ref'], decode_timedelta=False)
    ds_target = xs.spatial.subset(ds_target, **config['diagregion'][dregion])

    # regrid
    args=config['regrid']['regrid_dataset'].copy()
    args['regridder_kwargs']['locstream_out']=False
    wl= f"{os.environ['SLURM_TMPDIR']}/weights/" if 'SLURM_TMPDIR' in os.environ else f"{config['paths']['tmpdir']}/weights/"
    ds_sim = xs.regrid_dataset(
        ds=ds_sim,
        ds_grid=ds_target,
        weights_location= wl ,
        **args
    )
    #mask nan
    mask=ds_target['tasmax'].isel(time=130, drop=True).notnull().compute()
    ds_sim=ds_sim.where(mask)

    # chunk
    ds_sim = ds_sim.chunk({d: config['chunks']['working'][d] for d in ds_sim.dims})
    ds_scen = ds_scen.chunk({d: config['chunks']['working'][d] for d in ds_scen.dims})

    sim_prop, sim_meas = xs.properties_and_measures(
                                ds=ds_sim,
                                dref_for_measure=ref_prop,
                                **config['diagnostics']['properties_and_measures']
                            )
    
    scen_prop, scen_meas = xs.properties_and_measures(
                            ds=ds_scen,
                            dref_for_measure=ref_prop,
                            **config['diagnostics']['properties_and_measures']
                        )
    for out, name in zip([sim_prop, sim_meas, scen_prop, scen_meas],['sim_prop','sim_meas','scen_prop','scen_meas']):
        out = out.chunk(config['chunks']['diag'])
        save(out, output[name])

    imp = xs.diagnostics.measures_improvement([sim_meas,scen_meas])
    save(imp, output['imp'])


