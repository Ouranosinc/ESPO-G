from pathlib import Path

configfile: "config/config.yaml"
region=config["custom"]["regions"].keys()

rule reference_DEFAULT:
    input:
        lambda wildcards: [
           Path(config['paths']['refdir'])/f"ref_{wildcards.region_name}_default.zarr"
            for region_name in region]
    params:
        ref=config['paths']['refdir']
    output:
        zarr_file=f"ref/ref_{{region_name}}_default.zarr"
    resources:
        n_workers=2,
        threads_per_worker=5,
        memory="25GB"
    script:
        "scripts/load_default_ref.py"

rule reference_NOLEAP:
    input:
        lambda wildcards: [
           Path(config['paths']['refdir'])/f"ref_{wildcards.region_name}_noleap.zarr"
            for region_name in region]
    params:
        ref=config['paths']['refdir']
    output:
        zarr_file=f"ref/ref_{{region_name}}_noleap.zarr"
    resources:
        n_workers=2,
        threads_per_worker=5,
        memory="25GB"
    script:
        "scripts/load_noleap_ref.py"

rule reference_360_DAY:
    input:
        lambda wildcards: [
           Path(config['paths']['refdir'])/f"ref_{wildcards.region_name}_360_day.zarr"
            for region_name in region]
    params:
        ref=config['paths']['refdir']
    output:
        zarr_file=f"ref/ref_{{region_name}}_360_day.zarr"
    resources:
        n_workers=2,
        threads_per_worker=5,
        memory="25GB"
    script:
        "scripts/load_360_day_ref.py"
