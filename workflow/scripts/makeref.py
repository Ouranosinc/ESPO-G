import xclim as xc
import xscen as xs
from copy import deepcopy
import geopandas as gpd
from workflow.scripts.utils import dask_cluster
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    ref=snakemake.wildcards.ref
    output=snakemake.output


    region=config['full_region'].copy()
    del region['tile_buffer']
    cat_ref = xs.search_data_catalogs(**config['extraction']['reference'][ref]['search_data_catalogs'])
    dc = cat_ref.popitem()[1]
    ds_ref = xs.extract_dataset(catalog=dc,
                                region=region, 
                                **config['extraction']['reference'][ref]['extract_dataset']
                                )['D']
    ds_ref = xs.clean_up(ds_ref, **config['extraction']['clean_up'])

    
    #fix encoding chunks issue
    for var in ds_ref.data_vars:
        if 'chunks' in ds_ref[var].encoding:
            del ds_ref[var].encoding['chunks']
            

    xs.save_to_zarr(ds_ref, output['ref'], **config['save_to_zarr'], rechunk=config['chunks']['workingXY'])

    # generate coords file to be able to unstack in concat_clean
    ds_ref = xs.utils.stack_drop_nans(
        ds_ref,
        ds_ref['tasmax'].isel(time=0, drop=True).notnull().compute(),
        **config['utils']['stack_drop_nans']
    )

    xs.save_to_zarr(ds_ref, output['ref_stack'], **config['save_to_zarr'], rechunk=config['chunks']['workingloc'])
