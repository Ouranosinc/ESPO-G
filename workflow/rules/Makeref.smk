from pathlib import Path


region=config["custom"]["regions"].keys()


rule reference_DEFAULT:
    output:
        Path(config['paths']['refdir'])/"ref_{region}_default.zarr"
    log:
        "logs/reference_DEFAULT_{region}"
    script:
        "/home/ocisse/ESPO-G-stage-snakemake/espo_snakemake/workflow/scripts/load_default_ref.py"

rule reference_NOLEAP:
    input:
        Path(config['paths']['refdir'])/"ref_{region}_default.zarr"
    output:
        Path(config['paths']['refdir'])/"ref_{region}_noleap.zarr"
    log:
        "logs/reference_NOLEAP_{region}"
    script:
        "/home/ocisse/ESPO-G-stage-snakemake/espo_snakemake/workflow/scripts/load_noleap_ref.py"

rule reference_360_DAY:
    input:
        Path(config['paths']['refdir'])/"ref_{region}_default.zarr"
    output:
        Path(config['paths']['refdir'])/"ref_{region}_360_day.zarr"
    log:
        "logs/reference_360_DAY_{region}"
    script:
        "/home/ocisse/ESPO-G-stage-snakemake/espo_snakemake/workflow/scripts/load_360_day_ref.py"

rule diagnostics:
    input:
        Path(config['paths']['refdir'])/"ref_{region}_default.zarr"
    output:
        "/jarre/scenario/ocisse/ESPO-G6-stage/diagnostics/ECMW-ERA5-Land_NAM/diag-ref-prop_ECMW-ERA5-Land_NAM_{region}.zarr"
    log:
        "logs/diagnostics_{region}"
    script:
        "/home/ocisse/ESPO-G-stage-snakemake/espo_snakemake/workflow/scripts/diagnostics.py"

