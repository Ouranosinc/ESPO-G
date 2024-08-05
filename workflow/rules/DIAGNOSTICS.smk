from pathlib import Path

home=config["paths"]["home"]
ruleorder: DIAGNOSTICS > diag_improved_et_heatmap > concatenation_diag > concatenation_final
rule DIAGNOSTICS:
    input:
        regridded_and_rechunked = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",
        final = Path(config['paths']['final'])/"NAM_SPLIT/{region}/day_{sim_id}_{region}_1950-2100.zarr",
        diag_ref_prop = Path(config['paths']['final'])/"diagnostics/{region}/ECMW-ERA5-Land_NAM/diag-ref-prop_ECMW-ERA5-Land_NAM_{region}.zarr"
    output:
        diag_sim_meas=temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS_diag-sim-meas_{sim_id}_{region}.zarr")),
        diag_scen_meas=temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS_diag-scen-meas_{sim_id}_{region}.zarr")),
        diag_sim_prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOSTICS_diag-sim-prop_{sim_id}_{region}.zarr")),
        diag_scen_prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOSTICS_diag-scen-prop_{sim_id}_{region}.zarr"))
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+",
        sim_id="([^_]*_){6}[^_]*"
    params:
        n_workers=3,
        threads_per_worker=5,
        memory_limit='20GB'
    threads: 15
    script:
        f"{home}workflow/scripts/DIAGNOSTICS.py"

rule concatenation_final:
    input:
        final = expand(Path(config['paths']['final'])/"NAM_SPLIT/{region}/day_{{sim_id}}_{region}_1950-2100.zarr",  region=list(config["custom"]["regions"].keys()))
    output:
        directory(Path(config['paths']['final'])/"FINAL/NAM/day_{sim_id}_NAM_1950-2100.zarr")
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    threads: 15
    script:
        f"{home}workflow/scripts/concatenation_final.py"

rule concatenation_diag:
    input:
        diag_meas_prop = expand(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS_{{level}}_{{sim_id}}_{region}.zarr", region=list(config["custom"]["regions"].keys())),
    output:
        directory(Path(config['paths']['final'])/"diagnostics/NAM/{sim_id}/{level}_{sim_id}_NAM.zar")
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    threads: 15
    script:
        f"{home}workflow/scripts/concatenation_diag.py"

rule diag_improved_et_heatmap:
    input:
       sim=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS_diag-sim-meas_{sim_id}_{region}.zarr",
       scen=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS_diag-scen-meas_{sim_id}_{region}.zarr"
    output:
        diag_heatmap=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOCTICS_diag-heatmap_{sim_id}_{region}.zarr")),
        diag_improved= temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOCTICS_diag-improved_{sim_id}_{region}.zarr"))
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+",
        sim_id= "([^_]*_){6}[^_]*"
    params:
        n_workers=3,
        threads_per_worker=5,
        memory_limit='20GB'
    threads: 15
    script:
        f"{home}workflow/scripts/diag_improved_et_heatmap.py"



