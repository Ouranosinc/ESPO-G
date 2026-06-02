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
    input_noleap = snakemake.input.noleap
    input_360_day = snakemake.input.day360
    input_rechunk = snakemake.input.rechunk
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)

    client = dask_cluster(snakemake.params, config['dask']['client'])

    # load hist ds (simulation)
    ds_hist = xr.open_zarr(input_rechunk, decode_timedelta=False)

    if 'hursmin' in ds_hist:
        # trick for biasadjustement of hursmin (sim) on hursTasmax (ref)
        ds_hist = ds_hist.rename({'hursmin': 'hursTasmax'})

        # needed until we can use numpy>2, for clip in additive transform
        # ds_hist['hursTasmax'] = ds_hist['hursTasmax'].astype(float)
        # ds_hist['hurs'] = ds_hist['hurs'].astype(float)

    # load ref ds
    # choose right calendar
    simcal = xc.core.calendar.get_calendar(ds_hist)
    refcal = xs.utils.minimum_calendar(simcal, 'noleap')

    # snakemake can't have 360_day as a keyword..
    input_cal = input_noleap if refcal == 'noleap' else \
        input_360_day if refcal == '360_day' else 'unknown'
    ds_ref = xr.open_zarr(input_cal, decode_timedelta=False)

    # TODO: cheat temporarily until merge https://github.com/Ouranosinc/xsdba/pull/291
    ds_ref = ds_ref.expand_dims(
        {'realization': len(ds_hist.realization)}).chunk({"realization": -1})

    # training
    ds_tr = xs.train(
        dref=ds_ref,
        dhist=ds_hist,
        var=[var],
        **config['biasadjust']['variables'][var]['training_args']
    )

    for v in ['lat', 'lon']:
        del ds_tr[v].encoding['chunks']

    xs.save_to_zarr(
        ds_tr,
        output,
        rechunk=config['chunks']['workingloc'],
        **config['save_to_zarr'],
    )
