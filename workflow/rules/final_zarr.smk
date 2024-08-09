from pathlib import Path

home=config["paths"]["home"]

rule final_zarr:
    input:
        clean_up=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_cleaned_up.zarr",
        regridded=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regridded.zarr"
    output:
        directory(Path(config['paths']['final'])/"NAM_SPLIT/{region}/day_{sim_id}_{region}_1950-2100.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+",
        sim_id= "([^_]*_){6}[^_]*"
    params:
        threads_per_worker= lambda wildcards,threads, resources: threads / resources.n_workers,
        memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    resources:
        mem='40GB',
        n_workers=4,
        time=120
    threads: 4
    script:
        f"{home}workflow/scripts/final_zarr.py"
