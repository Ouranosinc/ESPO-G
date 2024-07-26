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
        n_workers=8,
        threads=5
    threads: 40
    resources:
        mem_mb=40000
    script:
        f"{home}workflow/scripts/health_check.py"