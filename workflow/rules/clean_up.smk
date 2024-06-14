from pathlib import Path

home=config["paths"]["home"]

region_name = list(config["custom"]["regions"].keys())
sim_id_name = wildcards_sim_id()

rule clean_up:
   input:
       expand(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{{sim_id}}_{{region}}_{var}_adjusted.zarr",var=["pr", "dtr", "tasmax"])
       # Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_pr_adjusted.zarr",
       # Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_dtr_adjusted.zarr",
       # Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_tasmax_adjusted.zarr"
   output:
       directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_cleaned_up.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+"
   log:
        "logs/clean_up_{sim_id}_{region}"
   script:
        f"{home}workflow/scripts/clean_up.py"















