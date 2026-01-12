from copy import deepcopy
import xarray as xr
import os
import xscen as xs
from workflow.scripts.utils import dask_cluster, save
if 1==0: #trick vscode
    import snakemake



if __name__ == '__main__':

    # Get Snakemake parameters
    inputs = snakemake.input
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)

    client=dask_cluster(snakemake.params)
    
    ds = xr.open_mfdataset(inputs, engine='zarr', decode_timedelta=False)


    #FIXME: until this check is in xscen
    # check if number of nan along time is different from total or 0.
    for var in ds.data_vars:
        da = ds[var]
        l = da.sizes["time"]
        valid = da.notnull().sum(dim="time")
        if (~((valid== l) | (valid == 0))).any():
            raise ValueError(
                f"Variable {var} has at least one gridpoint with some (but not all) missing values along time dimension."
            )

    hc = xs.diagnostics.health_checks(
        ds=ds,
        **config['health_checks']['final'])

    hc.attrs.update(ds.attrs)

    save(hc, output)


