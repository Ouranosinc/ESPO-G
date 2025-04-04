import xclim as xc
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    cat_ref = xs.search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])
    dc = cat_ref.popitem()[1]
    ds_ref = xs.extract_dataset(catalog=dc,
                                region=CONFIG['custom']['full_region'],
                                **CONFIG['extraction']['reference']['extract_dataset']
                                )['D']
    ds_ref = xs.clean_up(ds_ref, **CONFIG['extraction']['reference']['clean_up'])
    #FIXME: when xscen/xsda can handle units correctly
    ds_ref['pr'] = xc.core.units.convert_units_to(ds_ref['pr'],
                                                    'kg m-2 s-1',
                                                    context='hydro')
    ds_ref= ds_ref.chunk({d: CONFIG['chunks']['working'][d] for d in ds_ref.dims})
    
    # fix problem encoding
    # for var in ds_ref.data_vars:
    #     del ds_ref[var].encoding['chunks']
    
    tmp_zarr_and_zip(ds_ref, snakemake.output.ref)

    # diagnostics
    ds_ref_prop, _ = xs.properties_and_measures(ds=ds_ref, **CONFIG['diagnostics']['properties_and_measures'])
    #ds_ref_prop = ds_ref_prop.chunk(CONFIG['custom']['concat_chunks'])
    tmp_zarr_and_zip(ds_ref_prop, snakemake.output.prop)