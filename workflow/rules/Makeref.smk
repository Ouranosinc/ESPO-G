from pathlib import Path

ruleorder: reference_DEFAULT > reference_NOLEAP > reference_360_DAY
configfile: "config/config.yaml"
region=config["custom"]["regions"].keys()

rule reference_DEFAULT:
    params:
        ref=config['paths']['refdir'],
        exec=config['paths']['exec_workdir']
    output:
        zarr_file= Path(config['paths']['refdir'])/"ref_{region_name}_noleap.zarr"
    resources:
        n_workers=2,
        threads_per_worker=5,
        memory="25GB"
    script:
        "scripts/load_default_ref.py"

rule reference_NOLEAP:
    params:
        ref=config['paths']['refdir']
    output:
        zarr_file=f"{{ref}}/ref_{{region_name}}_noleap.zarr"
    resources:
        n_workers=2,
        threads_per_worker=5,
        memory="25GB"
    script:
        "scripts/load_noleap_ref.py"

rule reference_360_DAY:
    params:
        ref=config['paths']['refdir']
    output:
        zarr_file=f"{{ref}}/ref_{{region_name}}_360_day.zarr"
    resources:
        n_workers=2,
        threads_per_worker=5,
        memory="25GB"
    script:
        "scripts/load_360_day_ref.py"
