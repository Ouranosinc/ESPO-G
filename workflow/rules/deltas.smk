from pathlib import Path

home=config["paths"]["home"]

rule climatological_mean:
    input:
        Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_{xrfreq}_climatology.zarr"
    output:
        directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_{xrfreq}_delta.zarr")
    log:
        "logs/climatological_mean_{sim_id}_{region}_{xrfreq}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*",
        region= r"[a-zA-Z]+_[a-zA-Z]+"
    script:
        f"{home}workflow/scripts/climatological_mean.py"

rule ensemble:
    input:
        indicators = Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_{xrfreq}_indicators.zarr",
        climatology = Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_{xrfreq}_climatology.zarr",
        abs_delta_1991_2020 = ,
        per_delta_1991_2020 =
    output:
        directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/NAM_{processing_level}_{variable}_{xrfreq}_{experiment}_ensemble.zarr")
    log:
        "logs/ensemble_NAM_{processing_level}_{variable}_{xrfreq}_{experiment}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*",
        region= r"[a-zA-Z]+_[a-zA-Z]+"
    script:
        f"{home}workflow/scripts/ensemble.py"

