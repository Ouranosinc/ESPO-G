from pathlib import Path
import os
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster
if 1==0: #trick vscode
    import snakemake

xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)

    # rechunk 
    # xs.io.rechunk(
    #       path_in=snakemake.input[0],
    #       path_out=snakemake.output[0],
    #       chunks_over_dim=CONFIG['chunks']['final'] ,
    #       temp_store=f"{os.environ['SLURM_TMPDIR']}/{snakemake.wildcards.sim_id}+{snakemake.wildcards.subregion}/",
    #       overwrite=True)

    # ds = xr.open_zarr(snakemake.input[0], decode_timedelta=False)
    # ds=ds.chunk({k:v for k,v in CONFIG['chunks']['working'].items() if k in ['time','loc']})
    # tmp_zarr_and_zip(ds, str(snakemake.output[0]))

