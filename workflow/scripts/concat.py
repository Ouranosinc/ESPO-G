from copy import deepcopy
import xarray as xr
import xscen as xs
import xclim as xc
from workflow.scripts.utils import  save
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    final=snakemake.input.final
    output=snakemake.output
    config = deepcopy(snakemake.config)

    list_dsR = []
    for files in range(len(final)):
        dsR = xr.open_zarr(final[files], decode_timedelta=False)
        dsR.lat.encoding.pop('chunks', None)
        dsR.lon.encoding.pop('chunks', None)
        list_dsR.append(dsR)

    if 'rlat' in dsR:
        dsC = xr.concat(list_dsR, 'rlat')
    else:
        dsC = xr.concat(list_dsR, 'lat')

    dsC.attrs['cat:domain'] = config['full_region']['name']
    dsC.attrs['cat:processing_level']= 'final'
    dsC.attrs.pop('intake_esm_dataset_key', None)
    dsC.attrs.pop('cat:path', None)

                        
    chunks=xs.utils.translate_time_chunk(
        config['chunks']['final'],
        calendar=dsC.time.dt.calendar,
        timesize=dsC.time.size,)
    
    

    for var in dsC.data_vars:
        #history should be a global attrs only

        # delete_tmp=True to avoid going over limit  of localscratch in 2300
        xs.save_to_zarr(dsC[[var]], output[var], **config['save_to_zarr'],
         zip_kwargs=dict(delete=True),
         rechunk=chunks)

