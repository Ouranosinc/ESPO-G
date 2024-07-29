from dask.distributed import Client, LocalCluster
from dask import config as dskconf
from pathlib import Path
import xarray as xr
import logging
import xscen as xs
from xscen.xclim_modules import conversions
from xscen import (CONFIG, measure_time, timeout)


xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    cluster = LocalCluster(n_workers=snakemake.params.n_workers, threads_per_worker=snakemake.params.threads_per_worker,
                           memory_limit=f"{snakemake.params. memory_limit}MB", **daskkws)
    client = Client(cluster)

    fmtkws = {'step': 'scen', 'dom_name': snakemake.wildcards.dom_name, 'sim_id': snakemake.wildcards.sim_id}
    logger.info(fmtkws)

    dict_input = xr.open_zarr(snakemake.input.scen)
    step_dict = CONFIG['off-diag']['steps']['scen']
    # iter over datasets in that setp

    with (
        client,
        measure_time(name=f'off-diag {snakemake.wildcards.dom_name} scen {snakemake.wildcards.sim_id}',
                     logger=logger),
        timeout(18000, task='off-diag')
    ):

        # unstack
        if step_dict['unstack']:
            ds_input = xs.utils.unstack_fill_nan(dict_input)
        else:
            ds_input = dict_input

        # cut the domain
        ds_input = xs.spatial.subset(ds_input.chunk({'time': -1}), **CONFIG['off-diag']['domains'][snakemake.wildcards.dom_name])

        dref_for_measure = None
        if 'dref_for_measure' in step_dict.keys():
            dref_for_measure = xr.open_zarr(snakemake.input.off_diag_ref_prop)

        if 'dtr' not in ds_input:
            ds_input = ds_input.assign(dtr=conversions.dtr_from_minmax(ds_input.tasmin, ds_input.tasmax))

        prop, meas = xs.properties_and_measures(
            ds=ds_input,
            dref_for_measure=dref_for_measure,
            to_level_prop=f'off-diag-scen-prop',
            to_level_meas=f'off-diag-scen-meas',
            **step_dict['properties_and_measures']
        )
        if prop:
            xs.save_to_zarr(prop, str(snakemake.output.prop),
                            itervar=True,
                            rechunk=CONFIG['custom']['rechunk']
                            )
        if meas:
            xs.save_to_zarr(meas, str(snakemake.output.meas),
                            itervar=True,
                            rechunk=CONFIG['custom']['rechunk']
                            )



