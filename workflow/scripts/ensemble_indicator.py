from dask import config as dskconf
import xarray as xr
import logging
from dask.diagnostics import ProgressBar
import xscen as xs
from xscen import CONFIG

xs.load_config("config/config.yaml")
logger = logging.getLogger('xscen')

if __name__ == '__main__':
    daskkws = CONFIG['dask'].get('client', {})
    dskconf.set(**{k: v for k, v in CONFIG['dask'].items() if k != 'client'})

    fmtkws = {'xrfreq': snakemake.wildcards.xrfreq, 'region':  'NAM'}
    logger.info(fmtkws)


    # one ensemble (file) per level, per xrfreq, per variable, per experiment
    for input in snakemake.input.indicator:
        for file in input:
            ind_dict = xr.open_zarr(file, decode_timedelta=False)
            with (
                    ProgressBar(),
                    xs.measure_time(name=f'ensemble- NAM {snakemake.wildcards.experiment}'
                                      f' indicators  {snakemake.wildcards.xrfreq} {snakemake.wildcards.variable}',logger=logger),
            ):
                ens = xs.ensembles.ensemble_stats(
                    datasets=ind_dict,
                    to_level= f'ensemble-indicators',
                    **CONFIG['ensemble']['ensemble_stats_xscen']
                )

                ens.attrs['cat:variable']= xs.catalog.parse_from_ds(ens, ["variable"])["variable"]
                ens.attrs['cat:var'] = snakemake.wildcards.variable # for final filename

                xs.save_to_zarr(ens, str(snakemake.output[0]))

            # large_move(exec_wdir, "ensemble", CONFIG['paths']['ensemble'], pcat)