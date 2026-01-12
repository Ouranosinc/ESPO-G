import xclim as xc
import xscen as xs
from copy import deepcopy
from workflow.scripts.utils import dask_cluster, save
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    output=snakemake.output


    cat_ref = xs.search_data_catalogs(**config['extraction']['reference']['search_data_catalogs'])
    dc = cat_ref.popitem()[1]
    ds_ref = xs.extract_dataset(catalog=dc,
                                region=config['custom']['full_region'],
                                **config['extraction']['reference']['extract_dataset']
                                )['D']
    ds_ref = xs.clean_up(ds_ref, **config['extraction']['clean_up'])
    
    #fix encoding chunks issue
    for var in ds_ref.data_vars:
        if 'chunks' in ds_ref[var].encoding:
            del ds_ref[var].encoding['chunks']
            
    ds_ref= ds_ref.chunk({d: config['chunks']['working'][d] for d in ds_ref.dims})

    save(ds_ref, output['ref'])

