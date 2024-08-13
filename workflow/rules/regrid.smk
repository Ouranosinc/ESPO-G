from pathlib import Path

home=config["paths"]["home"]

rule regrid:
   input:
        noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
        extract = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_extracted.zarr"
   output:
        temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regridded.zarr"))
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   params:
       threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
       memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
   resources:
        mem='48GB',
        cpus_per_task=9,
        n_workers=3
   script:
        f"{home}workflow/scripts/regrid.py"

