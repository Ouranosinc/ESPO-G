import xscen as xs
from xscen import CONFIG
import xclim as xc
import xarray as xr
from workflow.scripts.utils import dask_cluster

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':
    client=dask_cluster(snakemake.params)

    ds_ref = xr.open_zarr(snakemake.input[0], decode_timedelta=False)
    
    ds_ref = xc.core.calendar.convert_calendar(ds_ref, snakemake.wildcards.calendar, align_on="year")

    xs.save_to_zarr(ds_ref, snakemake.output[0])