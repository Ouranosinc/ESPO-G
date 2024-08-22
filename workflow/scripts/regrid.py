import xarray as xr
import xscen as xs
import os
import xclim as xc
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':
    
    client=dask_cluster(snakemake.params)

    ds_input = xr.open_zarr(snakemake.input.extract, decode_timedelta=False)

    ds_target = xr.open_zarr(snakemake.input.noleap, decode_timedelta=False)

    ds_regrid = xs.regrid_dataset(
        ds=ds_input,
        ds_grid=ds_target,
        weights_location=f"{os.environ['SLURM_TMPDIR']}/weights/"
    )

    # chunk time dim
    ds_regrid = ds_regrid.chunk(
        xs.utils.translate_time_chunk({'time': '4year'},
                             xc.core.calendar.get_calendar(ds_regrid),
                             ds_regrid.time.size)
                               )

    # save
    xs.save_to_zarr(ds_regrid, str(snakemake.output[0]))
