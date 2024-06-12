from pathlib import Path

home=config["paths"]["home"]

rule DIAGNOSTICS:
    input:
        regridded_and_rechunked = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",
        final = Path(config['paths']['output_snakemake'])/"NAM_SPLIT/{region}/day_{sim_id}_{region}_{var}_1950-2100.zarr",
        diag_ref_prop = Path(config['paths']['final'])/"diagnostics/NAM/ECMWF-ERA5-Land_NAM/diag-ref-prop_ECMWF-ERA5-Land_NAM.zar"
    output:
        directory(Path(config['paths']['exec_diag_snakemake'])/"ESPO-G_workdir/{processing_level}_{sim_id}_{region}_{var}.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    log:
        "logs/DIAGNOSTICS_{processing_level}_{sim_id}_{region}_{var}"
    script:
        f"{home}workflow/scripts/DIAGNOSTICS.py"
