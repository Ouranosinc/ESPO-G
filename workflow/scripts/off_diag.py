import xarray as xr
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster
from xscen.xclim_modules import conversions

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':
    client=dask_cluster(snakemake.params)

    step=snakemake.params.step
    step_dict=CONFIG['off-diag']['steps'][step]


    ds_input = xr.open_zarr(snakemake.input.inp, decode_timedelta=False)
    
    if step_dict['unstack']:
            ds_input = xs.utils.unstack_fill_nan(ds_input)

    # cut the domain
    ds_input = xs.spatial.subset(
        ds_input.chunk({'time': -1}),
         **CONFIG['off-diag']['domains'][snakemake.wildcards.diag_domain])

    if 'dtr' not in ds_input:
            ds_input = ds_input.assign(dtr=conversions.dtr_from_minmax(ds_input.tasmin, ds_input.tasmax))

    dref_for_measure = None
    if getattr(snakemake.input, 'diag_ref_prop', False):
        dref_for_measure = xr.open_zarr(snakemake.input.diag_ref_prop, decode_timedelta=False)

    prop, meas = xs.properties_and_measures(
        ds=ds_input,
        dref_for_measure=dref_for_measure,
        **step_dict['properties_and_measures']
    )
    
    xs.save_to_zarr(prop, snakemake.output.prop, itervar=True, rechunk=CONFIG['custom']['final_chunks'])
    if meas:
        xs.save_to_zarr(meas, snakemake.output.meas, itervar=True, rechunk=CONFIG['custom']['final_chunks'])