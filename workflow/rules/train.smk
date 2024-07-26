from pathlib import Path

home=config["paths"]["home"]

rule train:
   input:
        noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
        day360 = Path(config['paths']['final'])/"reference/ref_{region}_360_day.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",
   output:
       directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_training.zarr")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   params:
       n_workers=4,
       threads=3
   resources:
       mem_mb=60000
   threads: 12
   script:
        f"{home}workflow/scripts/train.py"
