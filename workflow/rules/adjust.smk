from pathlib import Path

home=config["paths"]["home"]

rule adjust:
   input:
        train = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_training.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",
   output:
       directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_adjusted.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+"
   log:
        "logs/adjust_{sim_id}_{region}_{var}"
   script:
        f"{home}workflow/scripts/adjust.py"