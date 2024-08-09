from pathlib import Path

home=config["paths"]["home"]

rule train:
   input:
        noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
        day360 = Path(config['paths']['final'])/"reference/ref_{region}_360_day.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",
   output:
       temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_training.zarr"))
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   params:
       threads_per_worker=lambda wildcards, threads, resources: threads / resources.n_workers,
       memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
   threads: 8
   resources:
        time=60,
        n_workers=4,
        mem='40GB'
   script:
        f"{home}workflow/scripts/train.py"
