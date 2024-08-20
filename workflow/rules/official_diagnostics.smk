from pathlib import Path

home=config["paths"]["home"]

rule off_diag_ref_prop:
    input:
        ref=official_diags_inputfiles_ref
    output:
        prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-prop+{sim_id}+{dom_name}.zarr"))
    # params:
    #     threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     mem='60GB',
    #     n_workers=3,
    #     cpus_per_task=15,
    #     time=60
    # resources:
    #     mem_mb=60000
    params:
        threads_per_worker=5,
        memory_limit="20GB",
        n_workers=3,
        mem='60GB',
        cpus_per_task=15,
        time=170
    # wildcard_constraints:
    #     sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/off_diag_ref_prop.py"

rule off_diag_sim_prop_meas:
    input:
        off_diag_ref_prop = Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-prop+{sim_id}+{dom_name}.zarr",
        sim = official_diags_inputfiles_sim
    output:
        prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-sim-prop+{sim_id}+{dom_name}.zarr")),
        meas=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-sim-meas+{sim_id}+{dom_name}.zarr"))
    # params:
    #     threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     mem="60GB",
    #     cpus_per_task=15,
    #     n_workers=3
    # resources:
    #     mem_mb=60000
    params:
        threads_per_worker=5,
        memory_limit="20GB",
        n_workers=3,
        mem='60GB',
        cpus_per_task=15,
        time=170
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/off_diag_sim_prop_meas.py"

rule off_diag_scen_prop_meas:
    input:
        off_diag_ref_prop = Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-prop+{sim_id}+{dom_name}.zarr",
        scen = Path(config['paths']['final'])/"FINAL/NAM/day+{sim_id}+NAM_1950-2100.zarr"
    output:
        prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-scen-prop+{sim_id}+{dom_name}.zarr")),
        meas=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-scen-meas+{sim_id}+{dom_name}.zarr"))
    # params:
    #     threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     mem='60GB',
    #     cpus_per_task=15,
    #     n_workers=3
    # resources:
    #     mem_mb=60000
    params:
        threads_per_worker=5,
        memory_limit="20GB",
        n_workers=3,
        mem='60GB',
        cpus_per_task=15,
        time=170
    # wildcard_constraints:
    #     sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/off_diag_scen_prop_meas.py"

rule diag_measures_improvement:
    input:
        sim=Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-sim-meas+{sim_id}+{dom_name}.zarr",
        scen=Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-scen-meas+{sim_id}+{dom_name}.zarr"
    output:
        temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved+{sim_id}+{dom_name}.zarr"))
    # params:
    #     threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     mem='6GB',
    #     cpus_per_task=15,
    #     n_workers=3
    # resources:
    #     mem_mb=6000
    params:
        threads_per_worker=5,
        memory_limit="2GB",
        n_workers=3,
        mem='6GB',
        cpus_per_task=15,
        time=170
    # wildcard_constraints:
    #     sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/diag_measures_improvement.py"