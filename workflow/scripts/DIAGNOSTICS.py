from dask.distributed import Client
from dask import config as dskconf
import xarray as xr
import logging
import xscen as xs
from xscen import (
    CONFIG,
    measure_time, timeout)

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})


    fmtkws = {'region_name': snakemake.wildcards.region, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    with (
        Client(n_workers=3, threads_per_worker=5,
               memory_limit="20GB", **daskkws),
        measure_time(name=f'diagnostics', logger=logger),
        timeout(2 * 18000, task='diagnostics')
    ):
        for step, step_dict in CONFIG['diagnostics'].items():
            if step == "sim":
                ds_input = xr.open_zarr(snakemake.input.regridded_and_rechunked).chunk({'time': -1})

                dref_for_measure = None
                if 'dref_for_measure' in step_dict:
                    dref_for_measure = xr.open_zarr(snakemake.input.diag_ref_prop)

                prop, meas = xs.properties_and_measures(
                    ds=ds_input,
                    dref_for_measure=dref_for_measure,
                    to_level_prop=f'diag-{step}-prop',
                    to_level_meas=f'diag-{step}-meas',
                    **step_dict['properties_and_measures']
                )

                for ds in [prop, meas]:
                    xs.save_to_zarr(ds=ds, filename=str(snakemake.output[0]),
                                    rechunk=CONFIG['custom']['rechunk'],
                                    mode="o",
                                    itervar=True
                                    )
            else:
                ds_input = xr.open_zarr(snakemake.input.final).chunk({'time': -1})

                dref_for_measure = None
                if 'dref_for_measure' in step_dict:
                    dref_for_measure = xr.open_zarr(snakemake.input.diag_ref_prop)

                prop, meas = xs.properties_and_measures(
                    ds=ds_input,
                    dref_for_measure=dref_for_measure,
                    to_level_prop=f'diag-{step}-prop',
                    to_level_meas=f'diag-{step}-meas',
                    **step_dict['properties_and_measures']
                )

                for ds in [prop, meas]:
                    xs.save_to_zarr(ds, str(snakemake.output[0]),
                                    rechunk=CONFIG['custom']['rechunk'],
                                    mode="o",
                                    itervar=True
                                    )
