
import os
import xarray as xr
from xclim.core.calendar import  get_calendar 
import xscen as xs
from xscen import CONFIG
from xscen.utils import minimum_calendar
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml","config/config_region.yml","config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    
    xs.io.unzip_directory(snakemake.input.sim,f"{os.environ['SLURM_TMPDIR']}/dsim.zarr" )
    dsim= xr.open_zarr(f"{os.environ['SLURM_TMPDIR']}/dsim.zarr",decode_timedelta=False)

    # load ref ds
    refcal = minimum_calendar(get_calendar(dsim),CONFIG['biasadjust_mbcn']['maximal_calendar'])
    xs.io.unzip_directory(snakemake.input[f'ref_{refcal}'],f"{os.environ['SLURM_TMPDIR']}/dref.zarr")
    dref= xr.open_zarr(f"{os.environ['SLURM_TMPDIR']}/dref.zarr",decode_timedelta=False)


    dtrain=xs.train(dref,dsim,**CONFIG['biasadjust_mbcn']['train'])


    tmp_zarr_and_zip(dtrain,snakemake.output[0])
