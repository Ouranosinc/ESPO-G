import snakemake
import xscen as xs
from xscen import CONFIG
from utils import save_and_update, save_move_update
from pathlib import Path


exec_wdir = Path(CONFIG['paths']['exec_workdir'])
regriddir = Path(CONFIG['paths']['regriddir'])
refdir = Path(CONFIG['paths']['refdir'])

ref_source = CONFIG['extraction']['ref_source']

pcat = xs.ProjectCatalog(CONFIG['paths']['project_catalog'], create=True)

for region_name, region_dict in CONFIG['custom']['regions'].items():
    if (
            "makeref" in CONFIG["tasks"]
            and not pcat.exists_in_cat(domain=region_name, processing_level='nancount', source=ref_source)
    ):
        # default
        if not pcat.exists_in_cat(domain=region_name, source=ref_source):
                # search
                cat_ref = xs.search_data_catalogs(**CONFIG['extraction']['reference']['search_data_catalogs'])

                # extract
                dc = cat_ref.popitem()[1]
                ds_ref = xs.extract_dataset(catalog=dc,
                                            region=region_dict,
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
                ds_ref = ds_ref.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_ref.dims})

                save_move_update(ds=ds_ref,
                                 pcat=pcat,
                                 init_path=f"{exec_wdir}/ref_{region_name}_default.zarr",
                                 final_path=snakemake.output[0],
                                 info_dict={'calendar': 'default'
                                            })