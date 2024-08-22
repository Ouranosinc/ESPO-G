import os
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':
    
    client=dask_cluster(snakemake.params)

    xs.io.rechunk(path_in=str(snakemake.input[0]),
            path_out=str(snakemake.output[0]),
            chunks_over_dim=CONFIG['custom']['working_chunks'],
            temp_store=f"{os.environ['SLURM_TMPDIR']}/{snakemake.wildcards.sim_id}+{snakemake.wildcards.region}/",
            overwrite=True)
