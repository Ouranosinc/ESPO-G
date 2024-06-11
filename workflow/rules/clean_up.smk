from pathlib import Path
import xscen as xs

sim_id = wildcards_sim_id()
region=config["custom"]["regions"].keys()
home=config["paths"]["home"]

rule clean_up:
   output:
       directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_cleaned_up.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+"
   log:
        "logs/clean_up_{sim_id}_{region}"
   script:
        f"{home}workflow/scripts/clean_up.py"















