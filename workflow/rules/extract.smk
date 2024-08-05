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
   params:
        n_workers=2,
        threads_per_worker=5,
        memory_limit='25GB'
   threads: 10
   resources:
        mem_mb='50GB'
   script:
       f"{home}workflow/scripts/extract.py"