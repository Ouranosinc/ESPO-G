import xarray as xr
import xscen as xs
import xclim as xc
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config-general.yml", "config/config-region.yml", "config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    # load sim ds
    ds_sim = xr.open_zarr(snakemake.input.rechunk, decode_timedelta=False)
    ds_tr = xr.open_zarr(snakemake.input.train, decode_timedelta=False)
    

    # there are some negative dtr in the data (GFDL-ESM4). This puts is back to a very small positive.
    ds_sim['dtr'] = xc.sdba.processing.jitter_under_thresh(ds_sim.dtr, "1e-4 K")

    #TODO: test adapt
     # load ref ds
    # # choose right calendar
    # ds_sim=ds_sim.sel(time=slice('1951','2100'))
    # simcal = xc.core.calendar.get_calendar(ds_sim)
    # refcal = xs.utils.minimum_calendar(simcal, 'noleap')
    # input_cal = 'noleap' if refcal == 'noleap' else  'day360' if refcal == '360_day' else 'unknown'
    # ds_ref = xr.open_zarr(getattr(snakemake.input, input_cal), decode_timedelta=False)
    # ds_ref=ds_ref.convert_calendar(input_cal, align_on="year")
    # ds_sim=ds_sim.convert_calendar(input_cal, align_on="year")
    # group=xc.sdba.Grouper.from_kwargs(**CONFIG['biasadjust']['variables']['pr']['training_args']['group'])["group"]

    # #extend ref artificially to have same time has sim
    # ds_extended = xr.concat([ds_ref]*5, dim='time')
    # ds_extended['time']=ds_sim['time']

    # ds_extended=ds_extended.chunk({'time':-1})
    # ds_sim=ds_sim.chunk({'time':-1})

    # ds_sim['pr'],_,_ = xc.sdba.processing.adapt_freq(ds_extended['pr'], ds_sim['pr'], thresh="1 mm d-1",group=group)

    # adjust
    ds_scen = xs.adjust(
        dsim=ds_sim,
        dtrain=ds_tr,
        **CONFIG['biasadjust']['variables'][snakemake.wildcards.var]['adjusting_args']
        )

    xs.save_to_zarr(ds_scen, str(snakemake.output[0]))
