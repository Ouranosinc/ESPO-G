from pathlib import Path

home=config["paths"]["home"]

rule concat_FINAL:
    input:
        Path(config['paths']['final']) / "FINAL/NAM/day_{sim_id}_NAM_1950-2100.zarr"
    output:
        directory(Path(config['paths']['final']) / "checks/NAM/{sim_id}_NAM_checks.zarr")
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    log:
        "logs/health_check_{sim_id}_NAM"
    script:
        f"{home}workflow/scripts/health_check.py"