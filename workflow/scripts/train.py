from dask.distributed import Client
from dask import config as dskconf
import xarray as xr
import shutil
import logging
import xscen as xs
from xclim.core.calendar import get_calendar
from xscen import CONFIG
from pathlib import Path


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})
    #atexit.register(xs.send_mail_on_exit, subject=CONFIG['scripting']['subject'])

    cat_sim = xs.search_data_catalogs(
            **CONFIG['extraction']['simulation']['search_data_catalogs'])
    sim_id = list(cat_sim.keys())



    while True:  # if code bugs forever, it will be stopped by the timeout and then tried again
        try:
            with (
                # Client(n_workers=9, threads_per_worker=3, memory_limit="7GB", **daskkws),
                Client(n_workers=4, threads_per_worker=3,
                       memory_limit="15GB", **daskkws),
                xs.measure_time(name=f'train {snakemake.wildcards.var}', logger=logger),
                xs.timeout(18000, task='train')
            ):
                # load hist ds (simulation)
                ds_hist = xr.open_zarr(sim_id,
                                      snakemake.input.rechunk)

                # load ref ds
                # choose right calendar
                simcal = get_calendar(ds_hist)
                refcal = xs.utils.minimum_calendar(simcal, CONFIG['custom']['maximal_calendar'])
                if refcal== "defaut":
                    ds_ref = xr.open_zarr(snakemake.input.default)
                elif refcal == "noleap":
                    ds_ref = xr.open_zarr(snakemake.input.noleap)
                else:
                    ds_ref = xr.open_zarr(snakemake.input.day360)

                path_exec = Path(CONFIG['paths']['exec_workdir'])/"ESPO-G_workdir/ds_ref.zarr"
                # move to exec and reopen to help dask
                xs.save_to_zarr(ds_ref, str(path_exec), mode='o')
                ds_ref = xr.open_zarr(str(path_exec), decode_timedelta=False)

                # training
                ds_tr = xs.train(dref=ds_ref,
                                 dhist=ds_hist,
                                 var=[snakemake.wildcards.var],
                                 **conf['training_args'])

                ds_tr = ds_tr.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_tr.dims
                                     if d in CONFIG['custom']['chunks'].keys()})
                xs.save_to_zarr(ds_tr, str(snakemake.output[0])
                                )
                shutil.rmtree(str(path_exec))
        except xs.TimeoutException:
            pass
        else:
            break