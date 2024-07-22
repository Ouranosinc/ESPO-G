from dask.distributed import Client
from dask import config as dskconf
import xarray as xr
import logging
import numpy as np
import xscen as xs
from xclim.core.calendar import convert_calendar
import xclim as xc
from xscen import CONFIG

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    fmtkws = {'indicator': snakemake.wildcards.indname, 'sim_id': snakemake.wildcards.sim_id, 'region':  'NAM'}
    logger.info(fmtkws)

    ds_input = xr.open_zarr(snakemake.input.final)

    ds_input = ds_input.assign(tas=xc.atmos.tg(ds=ds_input))

    mod = xs.indicators.load_xclim_module(**CONFIG['indicators']['load_xclim_module'])
    dict_indname = dict(mod.iter_indicators())
    ind = dict_indname[snakemake.wildcards.indname]
    var_name = ind.cf_attrs[0]['var_name']
    freq = ind.injected_parameters['freq'].replace('YS', 'AS-JAN')

    with (
        Client(n_workers=2, threads_per_worker=3,
               memory_limit="30GB", **daskkws),
        xs.measure_time(name=f'indicators {snakemake.wildcards.sim_id}',
                        logger=logger),
        xs.timeout(20000, snakemake.wildcards.indname)
    ):
        if freq == '2QS-OCT':
            iAPR = np.where(ds_input.time.dt.month == 4)[0][0]
            dsi = ds_input.isel(time=slice(iAPR, None))
        else:
            dsi = ds_input
        if 'rolling' in ind.keywords or freq == 'QS-DEC':
            mult, *parts = xc.core.calendar.parse_offset(freq)
            steps = xc.core.calendar.construct_offset(mult * 8, *parts)
            for i, slc in enumerate(dsi.resample(time=steps).groups.values()):
                dsc = dsi.isel(time=slc)
                logger.info(f"Computing on slice {dsc.indexes['time'][0]}-{dsc.indexes['time'][-1]}.")
                _, out = xs.compute_indicators(
                    dsc,
                    indicators=[ind]).popitem()
                kwargs = {} if i == 0 else {'append_dim': 'time'}
                xs.save_to_zarr(out,
                                str(snakemake.output[0]),
                                rechunk={'time': -1},
                                mode='a',
                                zarr_kwargs=kwargs)
        else:
            _, out = xs.compute_indicators(
                dsi,
                indicators=[ind]).popitem()
            xs.save_to_zarr(out,
                            str(snakemake.output[0]),
                            rechunk={'time': -1},
                            mode='o')