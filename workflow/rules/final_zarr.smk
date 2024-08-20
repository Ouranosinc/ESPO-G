from pathlib import Path

home=config["paths"]["home"]

rule final_zarr:
    input:
        clean_up=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+cleaned_up.zarr",
        regridded=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+regridded.zarr"
    output:
        directory(Path(config['paths']['final'])/"NAM_SPLIT/{region}/day+{sim_id}+{region}+1950-2100.zarr")
    # wildcard_constraints:
    #     #region=r"[a-zA-Z]+_[a-zA-Z]+",
    #     sim_id= "([^_]*_){6}[^_]*"
    # params:
    #     threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     n_workers=2,
    #     mem='50GB',
    #     cpus_per_task=10,
    #     time=170
    # threads: 4
    # resources:
    #     mem_mb=50000
    params:
        threads_per_worker=5,
        memory_limit="25GB",
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time=170
    script:
        f"{home}workflow/scripts/final_zarr.py"
