import os
import xarray as xr
import xscen as xs
from xscen import CONFIG
from xscen.utils import stack_drop_nans
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml","config/config_region.yml","config/paths.yml")

if __name__ == '__main__':

    #client=dask_cluster(snakemake.params)

    # avoid opening the same file at the same time 
    #pathref=f"{os.environ['SLURM_TMPDIR']}/dref-{snakemake.wildcards.subregion}.zarr"
    #xs.io.unzip_directory(snakemake.input.ref, pathref)
    #ds_ref= xr.open_zarr(pathref,decode_timedelta=False)
    ds_ref= xr.open_zarr(snakemake.input.refstacked, decode_timedelta=False)

    # # stack
    # if CONFIG['custom']['stack_drop_nans']:

    #     variables = list(CONFIG['extraction']['reference']['search_data_catalogs'][
    #                             'variables_and_freqs'].keys())
    #     ds_ref = stack_drop_nans(
    #         ds_ref,
    #         ds_ref[variables[0]].isel(time=130, drop=True).notnull().compute(),
    #     )

    # cut region
    n=CONFIG['subregions']['n']
    r=int(snakemake.wildcards.subregion.replace(f"sr-",''))
    ds_ref=ds_ref.sel(loc=slice(n*r, n*(r+1)))

    ds_ref = ds_ref.chunk({d: CONFIG['chunks']['working'][d] for d in ds_ref.dims})
    ds_ref.attrs['cat:calendar'] = 'default'

    # fix problem encoding
    for var in list(ds_ref.data_vars)+list(ds_ref.coords):
        del ds_ref[var].encoding['chunks']

    tmp_zarr_and_zip(ds_ref,snakemake.output.default)

    # noleap
    ds_refnl =ds_ref.convert_calendar('noleap')
    ds_refnl.attrs['cat:calendar'] = 'noleap'
    tmp_zarr_and_zip(ds_refnl, snakemake.output.noleap)

    # 360_day
    ds_ref3 = ds_ref.convert_calendar('360_day', align_on="year")
    ds_ref3.attrs['cat:calendar'] = '360_day'
    tmp_zarr_and_zip(ds_ref3, snakemake.output.day360)