from copy import deepcopy
import xclim as xc
import xarray as xr
import xscen as xs
from workflow.scripts.utils import dask_cluster, save
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    output_prop = snakemake.output.prop
    input_ref= snakemake.input.ref
    dregion=snakemake.wildcards.dregion
    config = deepcopy(snakemake.config)

    client=dask_cluster(snakemake.params, config['dask']['client'])

    ds_ref= xr.open_zarr(input_ref,decode_timedelta=False)
    ds_ref = xs.spatial.subset(ds_ref, **config['diagregion'][dregion])

    # diagnostics
    with xr.set_options(keep_attrs=True): #FIXME: until xclim changes behavior, issue xclim #2308
        ds_ref_prop, _ = xs.properties_and_measures(ds=ds_ref, **config['diagnostics']['properties_and_measures'])
    ds_ref_prop = ds_ref_prop.chunk(config['chunks']['diag'])
    save(ds_ref_prop, output_prop)