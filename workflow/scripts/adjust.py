
import xarray as xr
import xclim as xc
from xclim.core.calendar import  get_calendar
import xscen as xs
from xscen.utils import minimum_calendar
from xscen import CONFIG
from workflow.scripts.utils import tmp_zarr_and_zip

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    # MBCn adjust fonctionne vrm mieux sans dask

    dsim= xr.open_zarr(snakemake.input.sim,decode_timedelta=False).load()

    refcal = minimum_calendar(get_calendar(dsim),CONFIG['biasadjust_mbcn']['maximal_calendar'])
    dref= xr.open_zarr(snakemake.input[f'ref_{refcal}'],decode_timedelta=False).load()
   
    dtrain= xr.open_zarr(snakemake.input.train,
                        decode_timedelta=False, 
                        drop_variables=['escores'],
                        ).load()

    ##FIXME: when xscen/xsda can handle units correctly
    dref['pr']=xc.units.convert_units_to(dref['pr'], 'kg m^-2 s^-1', context='hydro')
    dsim['pr']=xc.units.convert_units_to(dsim['pr'], 'kg m^-2 s^-1', context='hydro')

    out = xs.adjust(
        dtrain = dtrain, 
        dsim = dsim,
        dref = dref,
        **CONFIG['biasadjust_mbcn']['adjust'],
    )

    tmp_zarr_and_zip(out,snakemake.output[0])
