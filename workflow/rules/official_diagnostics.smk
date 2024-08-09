from pathlib import Path

home=config["paths"]["home"]

rule off_diag_ref_prop:
    input:
        ref=official_diags_inputfiles_ref
    output:
        prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-prop_{sim_id}_{dom_name}.zarr"))
    params:
        threads_per_worker= lambda wildcards,threads, resources: threads / resources.n_workers,
        memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    threads: 6
    resources:
        mem='30GB',
        n_workers=3,
        time=60
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/off_diag_ref_prop.py"

rule off_diag_sim_prop_meas:
    input:
        off_diag_ref_prop = Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-prop_{sim_id}_{dom_name}.zarr",
        sim = official_diags_inputfiles_sim
    output:
        prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-sim-prop_{sim_id}_{dom_name}.zarr")),
        meas=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-sim-meas_{sim_id}_{dom_name}.zarr"))
    params:
        threads_per_worker= lambda wildcards,threads, resources: threads / resources.n_workers,
        memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    threads: 9
    resources:
        mem="21GB",
        n_workers=3
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/off_diag_sim_prop_meas.py"

rule off_diag_scen_prop_meas:
    input:
        off_diag_ref_prop = Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-ref-prop_{sim_id}_{dom_name}.zarr",
        scen = Path(config['paths']['final'])/"FINAL/NAM/day_{sim_id}_NAM_1950-2100.zarr"
    output:
        prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-scen-prop_{sim_id}_{dom_name}.zarr")),
        meas=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-scen-meas_{sim_id}_{dom_name}.zarr"))
    params:
        threads_per_worker= lambda wildcards,threads, resources: threads / resources.n_workers,
        memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    threads: 15
    resources:
        mem='60GB',
        n_workers=3
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/off_diag_scen_prop_meas.py"

rule diag_measures_improvement:
    input:
        sim=Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-sim-meas_{sim_id}_{dom_name}.zarr",
        scen=Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/off-diag-scen-meas_{sim_id}_{dom_name}.zarr"
    output:
        temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved_{sim_id}_{dom_name}.zarr"))
    params:
        threads_per_worker= lambda wildcards,threads, resources: threads / resources.n_workers,
        memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    threads: 6
    resources:
        mem='6GB',
        n_workers=3
    wildcard_constraints:
        sim_id = "([^_]*_){6}[^_]*"
    script:
        f"{home}workflow/scripts/diag_measures_improvement.py"