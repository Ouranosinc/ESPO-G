import xarray as xr
import xscen as xs
import xclim as xc
from xscen import  CONFIG

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    list_dsR = []
    for files in range(len(snakemake.input.final)):
        dsR = xr.open_zarr(snakemake.input.final[files], decode_timedelta=False)
        dsR.lat.encoding.pop('chunks', None)
        dsR.lon.encoding.pop('chunks', None)
        list_dsR.append(dsR)

    if 'rlat' in dsR:
        dsC = xr.concat(list_dsR, 'rlat')
    else:
        dsC = xr.concat(list_dsR, 'lat')

    dsC.attrs['cat:domain'] = CONFIG['custom']['amno_region']['name']
    dsC.attrs.pop('intake_esm_dataset_key')

    dsC.attrs.pop('cat:path')

    # if xc.core.calendar.get_calendar(dsC.time) == '360_day':
    #     dsC = dsC.chunk({'time': 1440} | CONFIG['custom']['rechunk'])
    # else:
    #     dsC = dsC.chunk({'time': 1460} | CONFIG['custom']['rechunk'])

    dsC = dsC.chunk(
        xs.utils.translate_time_chunk(
            {'time': '4year'},
            xc.core.calendar.get_calendar(dsC),
            dsC.time.size)| CONFIG['custom']['final_chunks']
                               )

    xs.save_to_zarr(
        ds=dsC,
        filename=snakemake.output[0],
        )

