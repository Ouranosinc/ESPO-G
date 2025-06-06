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

    ds_ref= xr.open_zarr(snakemake.input[0], decode_timedelta=False)

    # cut region
    ds_ref = xs.spatial.subset(ds_ref, **CONFIG['custom']['regions'][snakemake.wildcards.subregion])

    # stack
    var = list(ds_ref.data_vars)[0]
    ds_ref = xs.utils.stack_drop_nans(
        ds_ref,
        ds_ref[var].isel(time=0, drop=True).notnull().compute(),
    )
    # chunk
    ds_ref = ds_ref.chunk({d: CONFIG['chunks']['working'][d] for d in ds_ref.dims})
    
    
    

    # fix problem encoding
    # for var in list(ds_ref.data_vars)+list(ds_ref.coords):
    #     del ds_ref[var].encoding['chunks']
    
    ds_ref.attrs['cat:calendar'] = 'default'
    tmp_zarr_and_zip(ds_ref,snakemake.output.default)

    # noleap
    ds_refnl =ds_ref.convert_calendar('noleap')
    ds_refnl.attrs['cat:calendar'] = 'noleap'
    tmp_zarr_and_zip(ds_refnl, snakemake.output.noleap)

    # 360_day
    ds_ref3 = ds_ref.convert_calendar('360_day', align_on="year")
    ds_ref3.attrs['cat:calendar'] = '360_day'
    tmp_zarr_and_zip(ds_ref3, snakemake.output.day360)