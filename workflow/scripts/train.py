from copy import deepcopy  # noqa: D100

import xarray as xr
import xclim as xc
import xscen as xs

from workflow.scripts.utils import dask_cluster


if 1 == 0:  # trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    var = snakemake.wildcards.var
    input_ref = snakemake.input.ref
    input_rechunk = snakemake.input.rechunk
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)

    client = dask_cluster(snakemake.params, config['dask']['client'])

    # load hist ds (simulation)
    ds_hist = xr.open_zarr(input_rechunk, decode_timedelta=False)

    if 'hursmin' in ds_hist:
        # trick for biasadjustement of hursmin (sim) on hursTasmax (ref)
        ds_hist = ds_hist.rename({'hursmin': 'hursTasmax'})

    # load ref ds
    # choose right calendar
    simcal = xc.core.calendar.get_calendar(ds_hist)
    refcal = xs.utils.minimum_calendar(simcal, 'noleap')

    ds_ref = xr.open_zarr(input_ref, decode_timedelta=False)
    ds_ref = ds_ref.convert_calendar(refcal, align_on="year")

    # training
    ds_tr = xs.train(
        dref=ds_ref,
        dhist=ds_hist,
        var=[var],
        **config['biasadjust']['variables'][var]['training_args']
    )

    xs.save_to_zarr(
        ds_tr,
        output,
        rechunk=config['chunks']['workingloc'],
        **config['save_to_zarr'],
    )
