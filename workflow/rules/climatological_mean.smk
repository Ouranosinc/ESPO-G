from pathlib import Path

home=config["paths"]["home"]

rule climatological_mean:
    input:
        Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_indicators.zarr"
    output:
        directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_climatology.zarr")
    log:
        "logs/climatological_mean_{sim_id}_NAM_{xrfreq}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*",
        region= r"[a-zA-Z]+_[a-zA-Z]+"
    script:
        f"{home}workflow/scripts/climatological_mean.py"