from pathlib import Path


region=config["custom"]["regions"].keys()


rule reference_DEFAULT:
    params:
        ref=config['paths']['refdir'],
        exec=config['paths']['exec_workdir']
    output:
        zarr_file= expand(Path(config['paths']['refdir'])/"ref_{region_name}_default.zarr", region_name=region)
    log:
        "logs/reference_DEFAULT"
    script:
        "/home/ocisse/ESPO-G-stage-snakemake/espo_snakemake/workflow/scripts/load_default_ref.py"

rule reference_NOLEAP:
    params:
        ref=config['paths']['refdir']
    output:
        zarr_file=expand(Path(config['paths']['refdir'])/"ref_{region_name}_noleap.zarr", region_name=region)
    log:
        "logs/reference_NOLEAP"
    script:
        "/home/ocisse/ESPO-G-stage-snakemake/espo_snakemake/workflow/scripts/load_noleap_ref.py"

rule reference_360_DAY:
    input:
        config['paths']['project_catalog']
    params:
        ref=config['paths']['refdir']
    output:
        Path(config['paths']['refdir'])/"ref_{region}_360_day.zarr"
    log:
        "logs/reference_360_DAY_{region}"
    script:
        "/home/ocisse/ESPO-G-stage-snakemake/espo_snakemake/workflow/scripts/load_360_day_ref.py"

rule diagnostics:
    input:
        config['paths']['project_catalog']
    output:
        "/jarre/scenario/ocisse/ESPO-G6-stage/diagnostics/ECMW-ERA5-Land_NAM/diag-ref-prop_ECMW-ERA5-Land_NAM_{region}.zarr"
    log:
        "logs/diagnostics_{region}"
    script:
        "/home/ocisse/ESPO-G-stage-snakemake/espo_snakemake/workflow/scripts/diagnostics.py"

