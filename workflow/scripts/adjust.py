
import xarray as xr
import xclim as xc
from xclim.core.calendar import  get_calendar
import xscen as xs
from xscen.utils import minimum_calendar
from xscen import CONFIG
from workflow.scripts.utils import tmp_zarr_and_zip
import numpy as np
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml","config/config_region.yml","config/paths.yml")

if __name__ == '__main__':

    # MBCn adjust fonctionne vrm mieux sans dask

    dsim= xr.open_zarr(snakemake.input.sim,decode_timedelta=False).load()
    
    # trick for biasadjustement of hursmin (sim) on hursTasmax (ref)
    if 'hursmin' in dsim:
        dsim = dsim.rename({'hursmin': 'hursTasmax'})

    refcal = minimum_calendar(get_calendar(dsim),CONFIG['biasadjust_mbcn']['maximal_calendar'])
    dref= xr.open_zarr(snakemake.input[f'ref_{refcal}'],decode_timedelta=False).load()
   
    dtrain= xr.open_zarr(snakemake.input.train,
                        decode_timedelta=False, 
                        drop_variables=['escores'],
                        ).load()

    out = xs.adjust(
        dtrain = dtrain, 
        dsim = dsim,
        dref = dref,
        **CONFIG['biasadjust_mbcn']['adjust'],
    )

    tmp_zarr_and_zip(out,snakemake.output[0])
