import xarray as xr
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':
    client=dask_cluster(snakemake.params)

    sim_id=snakemake.wildcards.sim_id
    diag_domain=snakemake.wildcards.diag_domain
    
    # get datasets
    meas_datasets = {}
    meas_datasets[f'{sim_id}.{diag_domain}.diag-sim-meas'] = xr.open_zarr(snakemake.input.sim, decode_timedelta=False)
    meas_datasets[f'{sim_id}.{diag_domain}.diag-scen-meas'] = xr.open_zarr(snakemake.input.scen,decode_timedelta=False)

    ip = xs.diagnostics.measures_improvement(meas_datasets)

    # save and update
    xs.save_to_zarr(ip, snakemake.output[0])
