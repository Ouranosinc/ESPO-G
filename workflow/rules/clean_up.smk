from pathlib import Path

home=config["paths"]["home"]

rule clean_up:
   input:
       expand(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{{sim_id}}_{{region}}_{var}_adjusted.zarr",var=["pr", "dtr", "tasmax"])
       # Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_pr_adjusted.zarr",
       # Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_dtr_adjusted.zarr",
       # Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_tasmax_adjusted.zarr"
   output:
       directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_cleaned_up.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   log:
        "logs/clean_up_{sim_id}_{region}"
   script:
        f"{home}workflow/scripts/clean_up.py"















