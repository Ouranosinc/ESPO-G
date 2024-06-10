from pathlib import Path

region=config["custom"]["regions"].keys()
home=config["paths"]["home"]

rule extract:
   output:
       Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/NAM_{region}_extracted.zarr"
   log:
        "logs/extract_NAM_{region}"
   script:
        f"{home}workflow/scripts/extract.py"
