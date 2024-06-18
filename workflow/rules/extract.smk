from pathlib import Path

home=config["paths"]["home"]

rule extract:
   output:
       directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_extracted.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   log:
        "logs/extract_{sim_id}_{region}"
   script:
        f"{home}workflow/scripts/extract.py"
