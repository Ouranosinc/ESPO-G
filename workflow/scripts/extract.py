from copy import deepcopy
from pathlib import Path
import xarray as xr
import xscen as xs
try:
    from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
except ImportError:
    from inpact.scripts.utils import save_to_zarrzip as tmp_zarr_and_zip
    from inpact.scripts.utils import dask_cluster
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    sim_id = snakemake.wildcards.sim_id
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)
    
    # Start Dask cluster
    client=dask_cluster(
        n_workers=snakemake.params.n_workers,
        cpus_per_task=snakemake.params.cpus_per_task,
        mem=snakemake.params.mem,
        local_directory=Path(config['tmppath']) / "dask",
        **config['dask'].get('client', {})
        )

    args = deepcopy(config['extraction']['simulation']['search_data_catalogs'])
    args['other_search_criteria'] = {'id': sim_id}
    # Search catalog
    cat_sim_id = xs.search_data_catalogs(**args,)

    # Extract
    dc_id = cat_sim_id.popitem()[1]
    ds_dict = xs.extract_dataset(catalog=dc_id,
                                 region=config['custom']['full_region'],
                                 **config['extraction']['simulation']['extract_dataset'],  # FIXME: Rename 'custom'?
                                 )
    ds_sim = ds_dict["D"]

    # Add fixed fields as coordinates
    if 'fx' in ds_dict:
        ds_sim = xr.merge([ds_sim, ds_dict['fx']], compat="override").assign_coords(ds_dict['fx'].data_vars)

    # Clean up time
    ds_sim['time'] = ds_sim.time.dt.floor('D')

    # Add the mask if not present
    if 'mask' not in ds_sim and 'create_mask' in config['extraction']['simulation']:
        ds_sim["mask"] = xs.regrid.create_mask(ds_sim, **config['extraction']['simulation']['create_mask'])
        if "sftlf" in ds_sim:
            ds_sim = ds_sim.drop_vars("sftlf")

    ds_sim = xs.clean_up(ds_sim, **config['extraction']['clean_up'])
    # Save to zarr
    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(ds_sim, output, rechunk=config['chunks']['pre-regrid'], encoding={v: {"dtype": "float32"} for v in ds_sim.data_vars})
    else:
        xs.save_to_zarr(ds_sim, output, rechunk=config['chunks']['pre-regrid'], encoding={v: {"dtype": "float32"} for v in ds_sim.data_vars})
