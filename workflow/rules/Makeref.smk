from pathlib import Path

region_name=list(config["custom"]["regions"].keys())
home=config["paths"]["home"]

rule reference_DEFAULT:
    output:
        directory(Path(config['paths']['final'])/"reference/ref_{region}_default.zarr")
    # wildcard_constraints:
    #     region=r"[a-zA-Z]+_[a-zA-Z]+"
    # resources:
    #     mem_mb=50000
    params:
        threads_per_worker=5,
        memory_limit="25GB",
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time=170
    script:
        f"{home}workflow/scripts/load_default_ref.py"

rule reference_NOLEAP:
    input:
        Path(config['paths']['final'])/"reference/ref_{region}_default.zarr"
    output:
        directory(Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr")
    # wildcard_constraints:
    #     region=r"[a-zA-Z]+_[a-zA-Z]+"
    # params:
    #     threads_per_worker= lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     mem='50GB',
    #     n_workers=2,
    #     cpus_per_task=10
    # resources:
    #     mem_mb=50000
    params:
        threads_per_worker=5,
        memory_limit="25GB",
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time=170
    script:
        f"{home}workflow/scripts/load_noleap_ref.py"

rule reference_360_DAY:
    input:
        Path(config['paths']['final'])/"reference/ref_{region}_default.zarr"
    output:
        directory(Path(config['paths']['final'])/"reference/ref_{region}_360_day.zarr")
    # wildcard_constraints:
    #     region=r"[a-zA-Z]+_[a-zA-Z]+"
    # params:
    #     threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     mem='50GB',
    #     n_workers=2,
    #     cpus_per_task=10
    # resources:
    #     mem_mb=50000
    params:
        threads_per_worker=5,
        memory_limit="25GB",
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time=170
    script:
        f"{home}workflow/scripts/load_360_day_ref.py"

rule diagnostics:
    input:
        Path(config['paths']['final'])/"reference/ref_{region}_default.zarr"
    output:
        directory(Path(config['paths']['final'])/"diagnostics/{region}/ECMW-ERA5-Land_NAM/diag-ref-prop+ECMW-ERA5-Land_NAM+{region}.zarr")
    # wildcard_constraints:
    #     region=r"[a-zA-Z]+_[a-zA-Z]+"
    # params:
    #     threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     mem='50GB',
    #     n_workers=2,
    #     cpus_per_task=10
    #threads: 2
    # resources:
    #     mem_mb=50000
    params:
        threads_per_worker=5,
        memory_limit="25GB",
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time=170
    script:
        f"{home}workflow/scripts/diagnostics.py"

rule concat_diag_ref_prop:
    input:
        diag=expand(Path(config['paths']['final'])/"diagnostics/{region}/ECMW-ERA5-Land_NAM/diag-ref-prop_ECMW-ERA5-Land_NAM_{region}.zarr", region=region_name)
    output:
        directory(Path(config['paths']['final'])/"diagnostics/NAM/ECMWF-ERA5-Land_NAM/diag-ref-prop_ECMWF-ERA5-Land_NAM.zar")
    # wildcard_constraints:
    #     region=r"[a-zA-Z]+_[a-zA-Z]+"
    # resources:
    #     mem_mb=50000
    params:
        threads_per_worker=5,
        memory_limit="25GB",
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time=170
    script:
        f"{home}workflow/scripts/concat.py"
