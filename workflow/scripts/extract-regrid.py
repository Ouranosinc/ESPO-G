import os
import copy
import xarray as xr
import xscen as xs
from xscen import CONFIG
import xclim as xc
from workflow.scripts.utils import  tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml","config/config_region.yml","config/paths.yml")

if __name__ == '__main__':

    args=copy.deepcopy(CONFIG['extraction']['simulation']['search_data_catalogs'])
    args['other_search_criteria'] = {'id': snakemake.wildcards.sim_id }
    # search cat
    cat_sim_id = xs.search_data_catalogs(**args,)

    # extract
    dc_id = cat_sim_id.popitem()[1]
    # buffer is need to take a bit larger than actual domain, to avoid weird effect at the edge
    # domain will be cut to the right shape during the regrid
    region_dict=CONFIG['full_region']
    region_dict['tile_buffer']=3
    ds_sim = xs.extract_dataset(catalog=dc_id,
                                region=region_dict,
                                **CONFIG['extraction']['simulation']['extract_dataset'],
                                )['D']
    ds_sim['time'] = ds_sim.time.dt.floor('D') # probably this wont be need when data is cleaned

    ds_sim = xs.clean_up(ds_sim, **CONFIG['extraction']['clean_up'])
    #FIXME: when xscen/xsda can handle units correctly, use clean_up only
    if 'pr' in ds_sim.data_vars:
        ds_sim['pr'] = xc.core.units.convert_units_to(ds_sim['pr'],
                                                        'kg m-2 s-1',
                                                        context='hydro')
    # need lat and lon -1 for the regrid
    ds_sim = ds_sim.chunk(CONFIG['chunks']['pre-regrid'])

    #REGRID

    ds_grid = xr.open_zarr(snakemake.input.noleap, decode_timedelta=False)

    ds_regrid = xs.regrid_dataset(
        ds=ds_sim,
        ds_grid=ds_grid,
        weights_location= f"{os.environ['SLURM_TMPDIR']}/weights/",
        **CONFIG['regrid']['regrid_dataset']
    )
    # chunk time dim
    ds_regrid = ds_regrid.chunk({d: CONFIG['chunks']['working'][d] for d in ds_regrid.dims})

    tmp_zarr_and_zip(ds_regrid,snakemake.output[0])