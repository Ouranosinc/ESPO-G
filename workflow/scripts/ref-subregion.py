import os
import xarray as xr
import xscen as xs
from copy import deepcopy
from xscen.utils import stack_drop_nans
from workflow.scripts.utils import dask_cluster, save
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs=snakemake.input
    output=snakemake.output
    subregion=snakemake.wildcards.subregion

    ds_ref= xr.open_zarr(inputs[0], decode_timedelta=False)

    # cut region
    ds_ref = xs.spatial.subset(ds_ref, **config['custom']['regions'][subregion])

    #TODO:might be nan in mask ? see remove_config branch

    # stack
    var = list(ds_ref.data_vars)[0]
    ds_ref = xs.utils.stack_drop_nans(
        ds_ref,
        ds_ref[var].isel(time=0, drop=True).notnull().compute(),
        **config['utils']['stack_drop_nans']
    )
    # chunk
    ds_ref = ds_ref.chunk({d: config['chunks']['working'][d] for d in ds_ref.dims})
    
    
    

    # fix problem encoding
    # for var in list(ds_ref.data_vars)+list(ds_ref.coords):
    #     del ds_ref[var].encoding['chunks']
    
    ds_ref.attrs['cat:calendar'] = 'default'
    save(ds_ref,output['default'])

    # noleap
    ds_refnl =ds_ref.convert_calendar('noleap')
    ds_refnl.attrs['cat:calendar'] = 'noleap'
    save(ds_refnl, output['noleap'])

    # 360_day
    ds_ref3 = ds_ref.convert_calendar('360_day', align_on="year")
    ds_ref3.attrs['cat:calendar'] = '360_day'
    save(ds_ref3, output['day360'])