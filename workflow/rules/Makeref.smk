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
        "scripts/load_default_ref.py"

rule reference_NOLEAP:
    params:
        ref=config['paths']['refdir']
    output:
        zarr_file=expand(Path(config['paths']['refdir'])/"ref_{region_name}_noleap.zarr", region_name=region)
    log:
        "logs/reference_NOLEAP"
    script:
        "scripts/load_noleap_ref.py"

rule reference_360_DAY:
    params:
        ref=config['paths']['refdir']
    output:
        zarr_file=expand(Path(config['paths']['refdir'])/"ref_{region_name}_360_day.zarr", region_name=region)
    log:
        "logs/reference_360_DAY"
    script:
        "scripts/load_360_day_ref.py"

rule drop_to_make_faster:
    input:
        config['paths']['project_catalog']
    output:
        rule_drop_to_make_faster_outfile
    log:
        "logs/drop_to_make_faster"
    script:
        "scripts/diagnostics.py"

