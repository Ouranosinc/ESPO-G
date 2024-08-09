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
       threads_per_worker=lambda wildcards, threads, resources: threads / resources.n_workers,
       memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
   threads: 8
   resources:
        mem="30GB",
        n_workers=2
   script:
        f"{home}workflow/scripts/rechunk.py"
