from pathlib import Path

var=config['biasadjust']['variables'].keys()
home=config["paths"]["home"]

rule train:
   input:
        default = Path(config['paths']['final'])/"reference/ref_{region}_default.zarr",
        noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
        day360 = Path(config['paths']['final'])/"reference/ref_{region}_360_day.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",
   output:
       directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_training.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+"
   log:
        "logs/train_{sim_id}_{region}_{var}"
   script:
        f"{home}workflow/scripts/train.py"