import xarray as xr
import os
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake


xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

if __name__ == '__main__':
    client=dask_cluster(snakemake.params)
    
    ds_input = xr.open_mfdataset(snakemake.input, engine='zarr', decode_timedelta=False)

    #FIXME: until this check is in xscen
    # check if number of nan along time is different from total or 0.
    for var in ds.data_vars:
        da = ds[var]
        ntime = da.sizes["time"]
        n_nan = da.isnull().sum(dim="time")
        if ((n_nan != 0) & (n_nan != ntime)).any():
            raise ValueError(
                f"Variable {var} has at least one gridpoint with some (but not all) missing values along time dimension."
            )

    hc = xs.diagnostics.health_checks(
        ds=ds_input,
        **CONFIG['health_checks']['final'])

    hc.attrs.update(ds_input.attrs)

    tmp_zarr_and_zip(hc, snakemake.output[0])


