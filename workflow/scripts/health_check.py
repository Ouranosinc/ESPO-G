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
    output_nam = snakemake.output["NAM"]
    output_qc = snakemake.output["QC"]
    config = deepcopy(snakemake.config)

    client = dask_cluster(snakemake.params, config["dask"]["client"])

    ds = xr.open_mfdataset(inputs, engine="zarr", decode_timedelta=False)

    hc = xs.diagnostics.health_checks(ds=ds, **config["health_checks"]["finalNAM"])

    hc.attrs.update(ds.attrs)

    xs.save_to_zarr(hc, output_nam, **config["save_to_zarr"])

    # more severe checks for QC region
    ds = xs.spatial.subset(ds, **config["QC"])
    hc = xs.diagnostics.health_checks(ds=ds, **config["health_checks"]["finalQC"])
    hc.attrs.update(ds.attrs)
    xs.save_to_zarr(hc, output_qc, **config["save_to_zarr"])
