from pathlib import Path
import shutil
import os
import xscen as xs
from xscen import CONFIG
from workflow.scripts.utils import dask_cluster

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    client=dask_cluster(snakemake.params)


    # rechunk 
    xs.io.rechunk(
          path_in=snakemake.input[0],
          path_out=snakemake.output[0],
          chunks_over_dim=CONFIG['custom']['final_chunks']|{'time': '4year'} ,
          temp_store=f"{os.environ['SLURM_TMPDIR']}/{snakemake.wildcards.sim_id}+{snakemake.wildcards.region}/",
          overwrite=True)



