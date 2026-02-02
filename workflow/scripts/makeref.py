from copy import deepcopy
import xarray as xr
import xscen as xs
try:
    from workflow.scripts.utils import tmp_zarr_and_zip
except ImportError:
    from inpact.scripts.utils import save_to_zarrzip as tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    output = snakemake.output.ref
    config = deepcopy(snakemake.config)

    # Case #1: Unique reference dataset
    if "search_data_catalogs" in config['extraction']['reference']:
        args = deepcopy(config['extraction']['reference'])

    # Case #2: Reference specified in Snakemake wildcards (loop the workflow over several references)
    else:
        reference = snakemake.wildcards.reference
        args = deepcopy(config['extraction']['reference'][reference])

    # Extract the reference dataset
    cat_ref = xs.search_data_catalogs(**args['search_data_catalogs'])
    dc = cat_ref.popitem()[1]
    ds_dict = xs.extract_dataset(catalog=dc,
                                 region=config['custom']['full_region'],  # FIXME: Rename 'custom'?
                                 **args['extract_dataset']
                                 )
    ds_ref = ds_dict["D"]

    # Add fixed fields as coordinates
    if 'fx' in ds_dict:
        ds_ref = xr.merge([ds_ref, ds_dict['fx']], compat="override").assign_coords(ds_dict['fx'].data_vars)
    
    # Clean up time
    ds_ref['time'] = ds_ref.time.dt.floor('D') 
    
    # Add the mask if not present
    if 'mask' not in ds_ref and 'create_mask' in args:
        ds_ref["mask"] = xs.regrid.create_mask(ds_ref, **args['create_mask'])
        if "sftlf" in ds_ref:
            ds_ref = ds_ref.drop_vars("sftlf")

    ds_ref = xs.clean_up(ds_ref, **config['extraction']['clean_up'])
    print(output)
    # FIXME: Shouldn't this be the final chunks?
    tmp_zarr_and_zip(ds_ref, output, rechunk=config['chunks']['working'], encoding={v: {"dtype": "float32"} for v in ds_ref.data_vars})
