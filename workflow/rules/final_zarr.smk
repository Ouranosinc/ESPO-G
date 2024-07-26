from pathlib import Path

home=config["paths"]["home"]

rule final_zarr:
    input:
        Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_cleaned_up.zarr"
    output:
        directory(Path(config['paths']['final'])/"NAM_SPLIT/{region}/day_{sim_id}_{region}_1950-2100.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+",
        sim_id= "([^_]*_){6}[^_]*"
    params:
        n_workers=4,
        threads=3
    resources:
        mem_mb=60000,
        time=30
    threads: 12
    script:
        f"{home}workflow/scripts/final_zarr.py"
