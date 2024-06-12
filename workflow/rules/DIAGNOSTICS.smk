from pathlib import Path

home=config["paths"]["home"]

rule DIAGNOSTICS:
    input:
        regridded_and_rechunked = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",
        final = Path(config['paths']['output_snakemake'])/"NAM_SPLIT/{region}/day_{sim_id}_{region}_1950-2100.zarr",
        diag_ref_prop = Path(config['paths']['final'])/"diagnostics/NAM/ECMWF-ERA5-Land_NAM/diag-ref-prop_ECMWF-ERA5-Land_NAM.zar"
    output:
        directory(expand(Path(config['paths']['exec_diag_snakemake'])/"ESPO-G_workdir/{level}_{sim_id}_{region}.zarr", level=['diag-sim-meas', 'diag-scen-meas', 'diag-sim-prop', 'diag-scen-prop']))
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    log:
        "logs/DIAGNOSTICS_{level}_{sim_id}_{region}"
    script:
        f"{home}workflow/scripts/DIAGNOSTICS.py"

rule diag_improved_et_heatmap:
    intput:
       expand(Path(config['paths']['exec_diag_snakemake'])/"ESPO-G_workdir/{level}_{sim_id}_{region}.zarr", level=['diag-sim-meas', 'diag-scen-meas'])
    output:
        directory(expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{processing_level}_{sim_id}_{region}.zarr", processing_level=['diag-improved', 'diag-heatmap']))
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    log:
        "logs/diag_improved_et_heatmap_{processing_level}_{sim_id}_{region}"
    script:
        f"{home}workflow/scripts/diag_improved_et_heatmap.py"