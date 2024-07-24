from pathlib import Path

region_name=list(config["custom"]["regions"].keys())
home=config["paths"]["home"]

rule reference_DEFAULT:
    output:
        directory(Path(config['paths']['final'])/"reference/ref_{region}_default.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    log:
        "logs/reference_DEFAULT_{region}"
    params:
        n_workers=2,
        threads=30
    resources:
        mem_mb=50000
    threads: 10
    script:
        f"{home}workflow/scripts/load_default_ref.py"

rule reference_NOLEAP:
    input:
        Path(config['paths']['final'])/"reference/ref_{region}_default.zarr"
    output:
        directory(Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    log:
        "logs/reference_NOLEAP_{region}"
    params:
        n_workers=2,
        threads=30
    resources:
        mem_mb=50000
    threads: 10
    script:
        f"{home}workflow/scripts/load_noleap_ref.py"

rule reference_360_DAY:
    input:
        Path(config['paths']['final'])/"reference/ref_{region}_default.zarr"
    output:
        directory(Path(config['paths']['final'])/"reference/ref_{region}_360_day.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    log:
        "logs/reference_360_DAY_{region}"
    params:
        n_workers=2,
        threads=30
    resources:
        mem_mb=50000
    threads: 10
    script:
        f"{home}workflow/scripts/load_360_day_ref.py"

rule diagnostics:
    input:
        Path(config['paths']['final'])/"reference/ref_{region}_default.zarr"
    output:
        directory(Path(config['paths']['final'])/"diagnostics/{region}/ECMW-ERA5-Land_NAM/diag-ref-prop_ECMW-ERA5-Land_NAM_{region}.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    log:
        "logs/diagnostics_{region}"
    params:
        n_workers=2,
        threads=30
    resources:
        mem_mb=50000
    threads: 10
    script:
        f"{home}workflow/scripts/diagnostics.py"

rule concat_diag_ref_prop:
   input:
       diag=expand(Path(config['paths']['final'])/"diagnostics/{region}/ECMW-ERA5-Land_NAM/diag-ref-prop_ECMW-ERA5-Land_NAM_{region}.zarr", region=region_name)
   output:
       directory(Path(config['paths']['final'])/"diagnostics/NAM/ECMWF-ERA5-Land_NAM/diag-ref-prop_ECMWF-ERA5-Land_NAM.zar")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+"
   log:
        "logs/concat_NAM"
   script:
        f"{home}workflow/scripts/concat.py"
