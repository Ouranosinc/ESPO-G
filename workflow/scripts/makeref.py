import xclim as xc
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml","config/config_region.yml","config/paths.yml")

if __name__ == '__main__':


    cat_ref = xs.search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])
    dc = cat_ref.popitem()[1]
    ds_ref = xs.extract_dataset(catalog=dc,
                                region=CONFIG['custom']['full_region'],
                                **CONFIG['extraction']['reference']['extract_dataset']
                                )['D']
    ds_ref = xs.clean_up(ds_ref, **CONFIG['extraction']['clean_up'])
    
    #fix encoding chunks issue
    for var in ds_ref.data_vars:
        if 'chunks' in ds_ref[var].encoding:
            del ds_ref[var].encoding['chunks']
            
    ds_ref= ds_ref.chunk({d: CONFIG['chunks']['working'][d] for d in ds_ref.dims})
    print(snakemake.output.ref)
    tmp_zarr_and_zip(ds_ref, snakemake.output.ref)

