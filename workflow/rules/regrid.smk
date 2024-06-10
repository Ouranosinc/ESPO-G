from pathlib import Path

region=config["custom"]["regions"].keys()
home=config["paths"]["home"]

rule regrid:
   input:
        noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
        extract = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/NAM_{region}_extracted.zarr"
   output:
        Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/NAM_{region}_regridded.zarr"
   log:
        "logs/regrid_NAM_{region}"
   script:
        f"{home}workflow/scripts/regrid.py"

