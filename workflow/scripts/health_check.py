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

    client=dask_cluster(snakemake.params,config['dask']['client'])
    
    ds = xr.open_mfdataset(inputs, engine='zarr', decode_timedelta=False)


    hc = xs.diagnostics.health_checks(
        ds=ds,
        **config['health_checks']['final'])

    hc.attrs.update(ds.attrs)

    save(hc, output)


