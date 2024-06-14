from pathlib import Path

home=config["paths"]["home"]

rule concatenation_final:
    input:
        ref = official_diags_inputfiles_ref,
        sim = official_diags_inputfiles_sim,
        scen = official_diags_inputfiles_scen
    output:
        directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{to_level}_{sim_id}_{dom_name}.zarr")
    log:
        "logs/official_diagnostics_{to_level}_{sim_id}_{dom_name}"
    script:
        f"{home}workflow/scripts/official_diagnostics.py"

rule diag_measurs_improvement:
    input:
