from pathlib import Path

home=config["paths"]["home"]

rule rechunk:
   input:
        Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regridded.zarr"
   output:
        directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   params:
       n_workers=2,
       threads_per_worker=5,
        memory_limit='30GB'
   threads: 15
   script:
        f"{home}workflow/scripts/rechunk.py"
