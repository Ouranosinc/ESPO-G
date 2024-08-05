from pathlib import Path

home=config["paths"]["home"]

rule train:
   input:
        noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
        day360 = Path(config['paths']['final'])/"reference/ref_{region}_360_day.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",
   output:
       temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_training.zarr"))
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+",
       sim_id="([^_]*_){6}[^_]*"
   params:
       n_workers=4,
       threads_per_worker=5,
       memory_limit='25GB'
   threads: 20
   resources:
        time=60
   script:
        f"{home}workflow/scripts/train.py"
