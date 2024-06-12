from pathlib import Path

home=config["paths"]["home"]

rule final_zarr:
    input:
        Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_cleaned_up.zarr"
    output:
        directory(Path(config['paths']['output_snakemake'])/"NAM_SPLIT/{region}/day_{sim_id}_{region}_{var}_1950-2100.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    log:
        "logs/final_zarr_{sim_id}_{region}_{var}"
    script:
        f"{home}workflow/scripts/final_zarr.py"
