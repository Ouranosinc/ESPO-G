import xarray as xr
import xscen as xs
from xscen import CONFIG
import xclim as xc
from workflow.scripts.utils import dask_cluster

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    # load hist ds (simulation)
    ds_hist = xr.open_zarr(snakemake.input.rechunk, decode_timedelta=False)

    # load ref ds
    # choose right calendar
    simcal = xc.core.calendar.get_calendar(ds_hist)
    refcal = xs.utils.minimum_calendar(simcal, CONFIG['custom']['maximal_calendar'])
    if refcal == "noleap":
        ds_ref = xr.open_zarr(snakemake.input.noleap, decode_timedelta=False)
    elif refcal == "360_day":
        ds_ref = xr.open_zarr(snakemake.input.day360, decode_timedelta=False)

    # training
    ds_tr = xs.train(
        dref=ds_ref,
        dhist=ds_hist,
        var=[snakemake.wildcards.var],
        **CONFIG['biasadjust']['variables'][snakemake.wildcards.var]['training_args']
        )

    ds_tr = ds_tr.chunk({d: CONFIG['custom']['working_chunks'][d] for d in ds_tr.dims
                            if d in CONFIG['custom']['working_chunks'].keys()})

    xs.save_to_zarr(ds_tr, str(snakemake.output[0]))
