from dask.distributed import Client
from dask import config as dskconf
import xarray as xr
import logging
import xscen as xs
from xclim.core.calendar import get_calendar
from xscen.utils import translate_time_chunk
from xscen import (
    CONFIG,
    regrid_dataset,
    measure_time
)


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    #atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])



# ---REGRID---
    # only works with xesmf 0.7

    with (
        # Client(n_workers=2, threads_per_worker=5,
        #        memory_limit="32GB", **daskkws),
            Client(n_workers=3, threads_per_worker=3, memory_limit="16GB", **daskkws),
            measure_time(name='regrid', logger=logger),
           #timeout(18000, task='regrid')
    ):

        ds_input = xr.open_zarr(snakemake.input.extract)

        ds_target = xr.open_zarr(snakemake.input.noleap)

        ds_regrid = regrid_dataset(
            ds=ds_input,
            ds_grid=ds_target, weights_location=f"{CONFIG['paths']['final']}workdir/weights/{snakemake.wildcards.region}"
        )

        #chunk time dim
        ds_regrid = ds_regrid.chunk(
            translate_time_chunk({'time': '4year'},
                                 get_calendar(ds_regrid),
                                 ds_regrid.time.size
                                )
                                    )

        # save
        xs.save_to_zarr(ds_regrid, str(snakemake.output[0]))
