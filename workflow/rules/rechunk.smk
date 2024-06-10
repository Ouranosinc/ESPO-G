from pathlib import Path

region=config["custom"]["regions"].keys()
home=config["paths"]["home"]

rule rechunk:
   input:
        Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/NAM_{region}_extracted.zarr"
   output:
        Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/NAM_{region}_regchunked.zarr"
   log:
        "logs/regchunked_NAM_{region}"
   script:
        f"{home}workflow/scripts/rechunk.py"
