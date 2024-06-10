from pathlib import Path

region=config["custom"]["regions"].keys()
var=config['biasadjust']['variables'].keys()
home=config["paths"]["home"]

rule train:
   input:
        default = Path(config['paths']['final'])/"reference/ref_{region}_default.zarr",
        noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
        day360 = Path(config['paths']['final'])/"reference/ref_{region}_360_day.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/NAM_{region}_regchunked.zarr",
   output:
       Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/NAM_{region}_{var}_training.zarr"
   log:
        "logs/train_{region}_{var}"
   script:
        f"{home}workflow/scripts/train.py"
