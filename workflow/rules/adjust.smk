from pathlib import Path

home=config["paths"]["home"]

rule adjust:
   input:
        train = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_training.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",
   output:
       temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_adjusted.zarr"))
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   params:
       threads_per_worker=lambda wildcards, threads, resources: int(threads / resources.n_workers),
       memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
   threads: 6
   resources:
        mem='40GB',
        n_workers=5,
   script:
        f"{home}workflow/scripts/adjust.py"

