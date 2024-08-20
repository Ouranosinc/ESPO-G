from pathlib import Path

home=config["paths"]["home"]

rule health_checks:
    input:
        Path(config['paths']['final']) / "FINAL/NAM/day+{sim_id}+NAM_1950-2100.zarr"
    output:
        directory(Path(config['paths']['final']) / "checks/NAM/{sim_id}+NAM_checks.zarr")
    # wildcard_constraints:
    #     sim_id = "([^_]*_){6}[^_]*"
    # params:
    #     threads_per_worker= lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # threads: 40
    # resources:
    #     mem='40GB',
    #     n_workers=8,
    #     cpus_per_task=40
    # resources:
    #     mem_mb=40000
    params:
        threads_per_worker=5,
        memory_limit="5GB",
        n_workers=8,
        mem='40GB',
        cpus_per_task=40,
        time=170
    script:
        f"{home}workflow/scripts/health_check.py"