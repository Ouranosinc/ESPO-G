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
       n_workers=5,
       threads_per_worker=3,
       memory_limit='12GB'
   threads: 20
   resources:
        mem='65GB'
   script:
        f"{home}workflow/scripts/adjust.py"

