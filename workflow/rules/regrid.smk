from pathlib import Path

home=config["paths"]["home"]

rule regrid:
   input:
        noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
        extract = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_extracted.zarr"
   output:
        directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regridded.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   params:
        n_workers=3,
        threads=3
   resources:
        mem_mb=48000
   threads: 9
   script:
        f"{home}workflow/scripts/regrid.py"

