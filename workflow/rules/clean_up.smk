from pathlib import Path

home=config["paths"]["home"]

rule clean_up:
   input:
        Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_adjusted.zarr"
   output:
       directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_cleaned_up.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+"
   log:
        "logs/clean_up_{sim_id}_{region}_{var}"
   script:
        f"{home}workflow/scripts/clean_up.py"















