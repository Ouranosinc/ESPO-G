"""Health checks on final datasets."""

from copy import deepcopy

import xarray as xr
import xscen as xs

from workflow.scripts.utils import dask_cluster


if 1 == 0:  # trick vscode
    import snakemake

if __name__ == "__main__":
    # Get Snakemake parameters
    inputs = snakemake.input
    config = deepcopy(snakemake.config)

    client = dask_cluster(snakemake.params, config["dask"]["client"])
    ds = xr.open_mfdataset(inputs, engine="zarr", decode_timedelta=False)

    for regionname, regionpath in snakemake.output.items():
        if regionname != config['full_region']['name']:
            ds = xs.spatial.subset(ds, **config[regionname])
        hc = xs.diagnostics.health_checks(ds=ds, **config["health_checks"][regionname])
        hc.attrs.update(ds.attrs)
        xs.save_to_zarr(hc, regionpath, **config["save_to_zarr"])