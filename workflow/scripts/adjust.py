import xarray as xr
import xscen as xs
import xclim as xc
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    # load sim ds
    ds_sim = xr.open_zarr(snakemake.input.rechunk, decode_timedelta=False)
    ds_tr = xr.open_zarr(snakemake.input.train, decode_timedelta=False)

    # there are some negative dtr in the data (GFDL-ESM4). This puts is back to a very small positive.
    ds_sim['dtr'] = xc.sdba.processing.jitter_under_thresh(ds_sim.dtr, "1e-4 K")

    # adjust
    ds_scen = xs.adjust(
        dsim=ds_sim,
        dtrain=ds_tr,
        **CONFIG['biasadjust']['variables'][snakemake.wildcards.var]['adjusting_args']
        )

    xs.save_to_zarr(ds_scen, str(snakemake.output[0]))
