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
       threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
       memory_limit=lambda wildcards, resources: f'{float(resources.mem.rstrip("GB")) / resources.n_workers}GB'
   resources:
        time=120,
        n_workers=3,
        cpus_per_task=12,
        mem='60GB'
   script:
        f"{home}workflow/scripts/train.py"
