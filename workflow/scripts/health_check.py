import xarray as xr
import os
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster


xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':
    client=dask_cluster(snakemake.params)
    
    ds_input = xr.open_zarr(snakemake.input[0], decode_timedelta=False)

    hc = xs.diagnostics.health_checks(
        ds=ds_input,
        **CONFIG['health_checks'])

    hc.attrs.update(ds_input.attrs)

    xs.save_to_zarr(hc, snakemake.output[0])


