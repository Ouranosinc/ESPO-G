
import xarray as xr
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    ds_input = xr.open_mfdataset(snakemake.input,engine='zarr',decode_timedelta=False)
    
    hc = xs.diagnostics.health_checks(ds=ds_input,)

    hc.attrs.update(ds_input.attrs)
    xs.save_to_zarr(ds=hc, filename=snakemake.output[0])
