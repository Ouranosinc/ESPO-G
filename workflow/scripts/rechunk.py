import os
import xscen as xs
from copy import deepcopy
import xarray as xr
from workflow.scripts.utils import dask_cluster, save
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':

    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs=snakemake.input
    output=snakemake.output[0]
    


    client=dask_cluster(snakemake.params, config['dask']['client'])

    # xs.io.rechunk(path_in=str(snakemake.input[0]),
    #         path_out=f"{os.environ['SLURM_TMPDIR']}/rechunked+{snakemake.wildcards.sim_id}+{snakemake.wildcards.subregion}/",
    #         chunks_over_dim={k:v for k,v in config['chunks']['working'].items() if k in ['time','loc']},
    #         temp_store=f"{os.environ['SLURM_TMPDIR']}/{snakemake.wildcards.sim_id}+{snakemake.wildcards.subregion}/",
    #         overwrite=True) # explicit parse_config magic if you uncomment this
    
    
    # # test to get rif of rechunker
    # ds = xr.open_zarr(f"{os.environ['SLURM_TMPDIR']}/rechunked+{snakemake.wildcards.sim_id}+{snakemake.wildcards.subregion}/",decode_timedelta=False)
    ds = xr.open_zarr(inputs[0],decode_timedelta=False)
    ds=ds.chunk({k:v for k,v in config['chunks']['working'].items() if k in ['time','loc']})

    #patch holes
    # ffill for the last time step.
    ds['tasmax']= ds['tasmax'].interpolate_na("time", method="linear").ffill("time")
    ds['tasmin']= ds['tasmin'].interpolate_na("time", method="linear").ffill("time")
    ds['dtr']= ds['dtr'].interpolate_na("time", method="linear").ffill("time")
    ds['pr'] = ds['pr'].where(ds['pr'].notnull(), other=0)

    # modify the code blabla

    #fix encoding chunks issue
    for var in ds.data_vars:
        if 'chunks' in ds[var].encoding:
            del ds[var].encoding['chunks']
    save(ds,output)
