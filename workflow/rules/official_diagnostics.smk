from pathlib import Path

home=config["paths"]["home"]

rule off_diag_ref_prop:
    input:
        official_diags_inputfiles_REF
    output:
        prop=directory(Path(
            config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-prop_{sim_id}_{dom_name}.zarr"),
        meas=directory(Path(
            config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-meas_{sim_id}_{dom_name}.zarr")
    log:
        "logs/off_diag_ref_prop_ref_{sim_id}_{dom_name}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/off_diag_ref_prop.py"

rule off_diag_sim_scen_prop:
    input:
        off_diag_ref_prop = Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-prop_{sim_id}_{dom_name}.zarr",
        sim = official_diags_inputfiles_sim,
        scen = official_diags_inputfiles_scen
    output:
        prop=directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-{step}-prop_{sim_id}_{dom_name}.zarr"),
        meas=directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-{step}-meas_{sim_id}_{dom_name}.zarr")
    log:
        "logs/official_diagnostics_{step}_{sim_id}_{dom_name}"
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/official_diagnostics.py"

# rule diag_measurs_improvement:
#     input:
