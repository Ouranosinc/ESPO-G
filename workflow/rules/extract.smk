from pathlib import Path

home=config["paths"]["home"]

rule extract:
   input:
       script=f"{home}workflow/scripts/extract.py"
   output:
       temp (directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_extracted.zarr"))
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   resources:
       n_workers=2,
       mem='50GB',
       cpus_per_task=10,
   params:
        threads_per_worker= lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
        memory_limit=lambda wildcards, resources: f'{float(resources.mem.rstrip("GB")) / resources.n_workers}GB'
   script:
       f"{home}workflow/scripts/extract.py"