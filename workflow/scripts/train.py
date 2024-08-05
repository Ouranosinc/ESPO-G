from dask.distributed import Client, LocalCluster
from dask.distributed import performance_report
from dask import config as dskconf
import xarray as xr
import shutil
import logging
from time import sleep
import xscen as xs
from xclim.core.calendar import get_calendar
from xscen import CONFIG
from pathlib import Path


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads_per_worker,
                           memory_limit=snakemake.params.memory_limit, **daskkws)
    client = Client(cluster)

    while True:  # if code bugs forever, it will be stopped by the timeout and then tried again
        try:
            with (
                xs.measure_time(name=f'train {snakemake.wildcards.var}', logger=logger),
                xs.timeout(18000, task='train'),
                performance_report(f"off-diag_{snakemake.wildcards.sim_id}.html")
            ):
                # load hist ds (simulation)
                ds_hist = xr.open_zarr(snakemake.input.rechunk)
                print(f'Taille de ds_hist: {ds_hist.sizes}, Taille des chunks: {ds_hist.chunks}')
                # load ref ds
                # choose right calendar
                simcal = get_calendar(ds_hist)
                refcal = xs.utils.minimum_calendar(simcal, CONFIG['custom']['maximal_calendar'])
                if refcal == "noleap":
                    ds_ref = xr.open_zarr(snakemake.input.noleap)
                    print(f'Taille de ds_ref: {ds_ref.sizes}, Taille des chunks: {ds_ref.chunks}')
                elif refcal == "360_day":
                    ds_ref = xr.open_zarr(snakemake.input.day360)
                    print(f'Taille de ds_ref: {ds_ref.sizes}, Taille des chunks: {ds_ref.chunks}')

                path_exec = Path(CONFIG['paths']['exec_workdir'])/"ESPO-G_workdir/ds_ref.zarr"
                # training
                ds_tr = xs.train(dref=ds_ref,
                                 dhist=ds_hist,
                                 var=[snakemake.wildcards.var],
                                 **CONFIG['biasadjust']['variables'][snakemake.wildcards.var]['training_args'])
                print(f'Taille de ds_tr: {ds_tr.sizes}, Taille des chunks: {ds_tr.chunks}')

                ds_tr = ds_tr.chunk({d: CONFIG['custom']['chunks'][d] for d in ds_tr.dims
                                     if d in CONFIG['custom']['chunks'].keys()})
                print(f'Taille de ds_tr chunké: {ds_tr.sizes}, Taille des chunks: {ds_tr.chunks}')

                sleep(120)
                xs.save_to_zarr(ds_tr, str(snakemake.output[0])
                                )

        except xs.TimeoutException:
            pass
        else:
            break