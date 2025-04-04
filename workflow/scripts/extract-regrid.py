import os
import copy
import xarray as xr
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import  tmp_zarr_and_zip

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    args=copy.deepcopy(CONFIG['extraction']['simulation']['search_data_catalogs'])
    args['other_search_criteria'] = {'id': snakemake.wildcards.sim_id +'_global'}
    # search cat
    cat_sim_id = xs.search_data_catalogs(**args,)

    # extract
    dc_id = cat_sim_id.popitem()[1]
    # buffer is need to take a bit larger than actual domain, to avoid weird effect at the edge
    # domain will be cut to the right shape during the regrid
    region_dict=CONFIG['custom']['full_region']
    region_dict['tile_buffer']=5
    ds_sim = xs.extract_dataset(catalog=dc_id,
                                region=region_dict,
                                **CONFIG['extraction']['simulation']['extract_dataset'],
                                )['D']
    ds_sim['time'] = ds_sim.time.dt.floor('D') # probably this wont be need when data is cleaned

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