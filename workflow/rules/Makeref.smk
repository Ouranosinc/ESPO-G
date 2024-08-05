from pathlib import Path

region_name=list(config["custom"]["regions"].keys())
home=config["paths"]["home"]

rule reference_DEFAULT:
    output:
        directory(Path(config['paths']['final'])/"reference/ref_{region}_default.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    params:
        n_workers=2,
        threads_per_worker=5,
        memory_limit='30GB'
    resources:
        mem_mb='60GB'
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
    params:
        n_workers=2,
        threads_per_worker=5,
        memory_limit='30GB'
    resources:
        mem_mb='65GB'
    threads: 15
    script:
        f"{home}workflow/scripts/load_noleap_ref.py"

rule reference_360_DAY:
    input:
        Path(config['paths']['final'])/"reference/ref_{region}_default.zarr"
    output:
        directory(Path(config['paths']['final'])/"reference/ref_{region}_360_day.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    params:
        n_workers=2,
        threads_per_worker=10,
        memory_limit='30GB'
    resources:
        mem_mb='65GB'
    threads: 25
    script:
        f"{home}workflow/scripts/load_360_day_ref.py"

rule diagnostics:
    input:
        Path(config['paths']['final'])/"reference/ref_{region}_default.zarr"
    output:
        directory(Path(config['paths']['final'])/"diagnostics/{region}/ECMW-ERA5-Land_NAM/diag-ref-prop_ECMW-ERA5-Land_NAM_{region}.zarr")
    wildcard_constraints:
        region=r"[a-zA-Z]+_[a-zA-Z]+"
    params:
        n_workers=2,
        threads_per_worker=10,
        memory_limit='30GB'
    resources:
        mem_mb='80GB'
    threads: 25
    script:
        f"{home}workflow/scripts/diagnostics.py"

rule concat_diag_ref_prop:
   input:
       diag=expand(Path(config['paths']['final'])/"diagnostics/{region}/ECMW-ERA5-Land_NAM/diag-ref-prop_ECMW-ERA5-Land_NAM_{region}.zarr", region=region_name)
   output:
       directory(Path(config['paths']['final'])/"diagnostics/NAM/ECMWF-ERA5-Land_NAM/diag-ref-prop_ECMWF-ERA5-Land_NAM.zar")
   wildcard_constraints:
       region = r"[a-zA-Z]+_[a-zA-Z]+"
   threads: 20
   script:
        f"{home}workflow/scripts/concat.py"
