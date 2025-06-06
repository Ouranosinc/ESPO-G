import os
import xscen as xs
from xscen import CONFIG
import xarray as xr
from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

if __name__ == '__main__':
    
    client=dask_cluster(snakemake.params)

    # xs.io.rechunk(path_in=str(snakemake.input[0]),
    #         path_out=str(snakemake.output[0]),
    #         chunks_over_dim={k:v for k,v in CONFIG['chunks']['working'].items() if k in ['time','loc']},
    #         temp_store=f"{os.environ['SLURM_TMPDIR']}/{snakemake.wildcards.sim_id}+{snakemake.wildcards.subregion}/",
    #         overwrite=True)
    # test to get rif of rechunker
    ds = xr.open_zarr(snakemake.input[0], decode_timedelta=False)
    ds=ds.chunk({k:v for k,v in CONFIG['chunks']['working'].items() if k in ['time','loc']})
    #fix encoding chunks issue
    for var in ds.data_vars:
        if 'chunks' in ds[var].encoding:
            del ds[var].encoding['chunks']
    xs.save_to_zarr(ds,snakemake.output[0])
