import xarray as xr
import xscen as xs
import xclim as xc
import xsdba as xa
from xscen import CONFIG
import numpy as np
from workflow.scripts.utils import dask_cluster, create_tmp_path
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    # load sim ds
    ds_sim = xr.open_zarr(snakemake.input.rechunk, decode_timedelta=False)
    ds_tr = xr.open_zarr(snakemake.input.train, decode_timedelta=False)

    if 'hursmin' in ds_sim:
        # trick for biasadjustement of hursmin (sim) on hursTasmax (ref)
        ds_sim = ds_sim.rename({'hursmin': 'hursTasmax'})
        #FIXME: needed until we can use numpy>2
        ds_sim['hursTasmax'] = ds_sim['hursTasmax'].astype(float)
        ds_sim['hurs'] = ds_sim['hurs'].astype(float)

    #TODO: clip tmp
    #ds_sim['hurs'] = ds_sim['hurs'].clip(0,100)
    #ds_sim['hursTasmax'] = ds_sim['hursTasmax'].clip(0,100)

    # there are some negative dtr in the data (GFDL-ESM4). This puts is back to a very small positive.
    ds_sim['dtr'] = xa.processing.jitter_under_thresh(ds_sim.dtr, "1e-4 K")

    # adjust
    ds_scen = xs.adjust(
        dsim=ds_sim,
        dtrain=ds_tr,
        **CONFIG['biasadjust']['variables'][snakemake.wildcards.var]['adjusting_args']
        )

    #final clip
    if 'hurs' in ds_scen:
        ds_scen['hurs'] = ds_scen['hurs'].clip(0,100)

    xs.save_to_zarr(ds_scen, str(snakemake.output[0]))
