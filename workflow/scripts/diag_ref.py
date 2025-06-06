import xclim as xc
import xarray as xr
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml","config/config_region.yml","config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    ds_ref= xr.open_zarr(snakemake.input.ref,decode_timedelta=False)
    ds_ref = xs.spatial.subset(ds_ref, **CONFIG['diagregion'][snakemake.wildcards.dregion])

    # diagnostics
    ds_ref_prop, _ = xs.properties_and_measures(ds=ds_ref, **CONFIG['diagnostics']['properties_and_measures'])
    ds_ref_prop = ds_ref_prop.chunk(CONFIG['chunks']['diag'])
    tmp_zarr_and_zip(ds_ref_prop, snakemake.output.prop)