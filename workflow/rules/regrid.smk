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
        n_workers=3,
        threads_per_worker=3,
        memory_limit='16GB'
   resources:
        mem='50GB'
   threads: 12
   script:
        f"{home}workflow/scripts/regrid.py"

