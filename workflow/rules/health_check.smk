from pathlib import Path

home=config["paths"]["home"]

rule health_checks:
    input:
        Path(config['paths']['final']) / "FINAL/NAM/day_{sim_id}_NAM_1950-2100.zarr"
    output:
        directory(Path(config['paths']['final']) / "checks/NAM/{sim_id}_NAM_checks.zarr")
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    params:
        threads_per_worker= lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
        memory_limit=lambda wildcards, resources: f'{float(resources.mem.rstrip("GB")) / resources.n_workers}GB'
    threads: 40
    resources:
        mem='40GB',
        n_workers=8,
        cpus_per_task=40
    script:
        f"{home}workflow/scripts/health_check.py"