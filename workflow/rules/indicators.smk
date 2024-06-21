from pathlib import Path

home=config["paths"]["home"]
indname_name = indname_name_func()

rule indicator:
    input:
        # final=Path(config['paths']['final'])/"NAM_SPLIT/{region}/day_{sim_id}_{region}_1950-2100.zarr"
        final = Path(config['paths']['final'])/"FINAL/NAM/day_{sim_id}_NAM_1950-2100.zarr"
    output:
        directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/tmp/{sim_id}_NAM_{indname}.zarr")
    log:
        "logs/indicators_{sim_id}_NAM_{indname}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*",
        region= r"[a-zA-Z]+_[a-zA-Z]+"
    script:
        f"{home}workflow/scripts/indicators.py"

rule iter_freq:
    input:
        file = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/tmp/{{sim_id}}_NAM_{indname}.zarr", indname=indname_name)
    output:
        directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_indicators.zarr")
    log:
        "logs/iter_freq_{sim_id}_NAM_{xrfreq}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*",
        region= r"[a-zA-Z]+_[a-zA-Z]+"
    script:
        f"{home}workflow/scripts/iter_freq.py"

