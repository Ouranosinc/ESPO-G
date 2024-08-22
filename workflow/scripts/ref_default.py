import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':
    client=dask_cluster(snakemake.params)

    # search
    cat_ref = xs.search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

    # extract
    dc = cat_ref.popitem()[1]

    ds_ref = xs.extract_dataset(catalog=dc,
                                region= CONFIG['custom']['regions'][snakemake.wildcards.region],
                                **CONFIG['extraction']['reference']['extract_dataset']
                                )['D']

    # stack
    if CONFIG['custom']['stack_drop_nans']:
        var = list(ds_ref.data_vars)[0]
        ds_ref = xs.utils.stack_drop_nans(
            ds_ref,
            ds_ref[var].isel(time=0, drop=True).notnull().compute(),
        )
    # chunk
    ds_ref = ds_ref.chunk({d: CONFIG['custom']['working_chunks'][d] for d in ds_ref.dims})

    xs.save_to_zarr(ds_ref, snakemake.output[0])