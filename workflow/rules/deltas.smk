from pathlib import Path

home=config["paths"]["home"]
sim_id_name = wildcards_sim_id()

rule delta:
    input:
        Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_climatology.zarr"
    output:
        abs_delta=directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_abs_delta.zarr"),
        per_delta=directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_per_delta.zarr")
    log:
        "logs/climatological_mean_{sim_id}_NAM_{xrfreq}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*",
        region= r"[a-zA-Z]+_[a-zA-Z]+"
    script:
        f"{home}workflow/scripts/deltas.py"

rule ensemble_indicator:
    input:
        indicator = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{{xrfreq}}_indicators.zarr",sim_id=sim_id_name)
    output:
        directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/NAM_{process_level}_{variable}_{xrfreq}_{experiment}_ensemble.zarr")
    log:
        "logs/ensemble_indicator_NAM_{process_level}_{variable}_{xrfreq}_{experiment}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*",
        region= r"[a-zA-Z]+_[a-zA-Z]+"
    script:
        f"{home}workflow/scripts/ensemble_indicator.py"

# rule ensemble_climatology:
#     input:
#         climatology = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{{xrfreq}}_climatology.zarr",sim_id=sim_id_name)
#     output:
#         directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/NAM_{process_level}_{variable}_{xrfreq}_{experiment}_ensemble.zarr")
#     log:
#         "logs/ensemble_climatology_NAM_{process_level}_{variable}_{xrfreq}_{experiment}"
#     wildcard_constraints:
#         sim_id = "([^_]*_){6}[^_]*",
#         region= r"[a-zA-Z]+_[a-zA-Z]+"
#     script:
#         f"{home}workflow/scripts/ensemble_climatology.py"
#
# rule ensemble_abs_delta:
#     input:
#         abs_delta_1991_2020 = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{{xrfreq}}_abs_delta.zarr",sim_id=sim_id_name)
#     output:
#         directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/NAM_{process_level}_{variable}_{xrfreq}_{experiment}_ensemble.zarr")
#     log:
#         "logs/ensemble_abs_delta_NAM_{process_level}_{variable}_{xrfreq}_{experiment}"
#     wildcard_constraints:
#         sim_id = "([^_]*_){6}[^_]*",
#         region= r"[a-zA-Z]+_[a-zA-Z]+"
#     script:
#         f"{home}workflow/scripts/ensemble_abs_delta.py"
#
# rule ensemble_per_delta:
#     input:
#         per_delta_1991_2020 = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{{xrfreq}}_per_delta.zarr",sim_id=sim_id_name)
#     output:
#         directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/NAM_{process_level}_{variable}_{xrfreq}_{experiment}_ensemble.zarr")
#     log:
#         "logs/ensemble_per_delta_NAM_{process_level}_{variable}_{xrfreq}_{experiment}"
#     wildcard_constraints:
#         sim_id = "([^_]*_){6}[^_]*",
#         region= r"[a-zA-Z]+_[a-zA-Z]+"
#     script:
#         f"{home}workflow/scripts/ensemble_per_delta.py"
