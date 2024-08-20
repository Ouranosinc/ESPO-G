from pathlib import Path

home=config["paths"]["home"]
ruleorder: DIAGNOSTICS > diag_improved_et_heatmap > concatenation_diag > concatenation_final
rule DIAGNOSTICS:
    input:
        regridded_and_rechunked = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+regchunked.zarr",
        final = Path(config['paths']['final'])/"NAM_SPLIT/{region}/day+{sim_id}+{region}+1950-2100.zarr",
        diag_ref_prop = Path(config['paths']['final'])/"diagnostics/{region}/ECMW-ERA5-Land_NAM/diag-ref-prop+ECMW-ERA5-Land_NAM+{region}.zarr"
    output:
        diag_sim_meas=temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS+diag-sim-meas+{sim_id}+{region}.zarr")),
        diag_scen_meas=temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS+diag-scen-meas+{sim_id}+{region}.zarr")),
        diag_sim_prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOSTICS+diag-sim-prop+{sim_id}+{region}.zarr")),
        diag_scen_prop=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOSTICS+diag-scen-prop+{sim_id}+{region}.zarr"))
    # wildcard_constraints:
    #     region=r"[a-zA-Z]+_[a-zA-Z]+",
    #     sim_id="([^_]*_){6}[^_]*"
    # params:
    #     threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     mem='60GB',
    #     n_workers=3,
    #     cpus_per_task=15
    params:
        threads_per_worker=5,
        memory_limit="30GB",
        n_workers=3,
        mem='60GB',
        cpus_per_task=15,
        time=170
    script:
        f"{home}workflow/scripts/DIAGNOSTICS.py"

# rule concatenation_final:
#     input:
#         final = expand(Path(config['paths']['final'])/"NAM_SPLIT/{region}/day+{{sim_id}}+{region}+1950-2100.zarr",  region=list(config["custom"]["regions"].keys()))
#     output:
#         directory(Path(config['paths']['final'])/"FINAL/NAM/day+{sim_id}+NAM_1950-2100.zarr")
#     # wildcard_constraints:
#     #     sim_id = "([^_]*_){6}[^_]*"
#     params:
#         threads_per_worker=1,
#         memory_limit="5GB",
#         n_workers=12,
#         mem='60GB',
#         cpus_per_task=12,
#         time=170
#     script:
#         f"{home}workflow/scripts/concatenation_final.py"

rule concatenation_diag:
    input:
        diag_meas_prop = expand(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS+{{level}}+{{sim_id}}+{region}.zarr", region=list(config["custom"]["regions"].keys())),
    output:
        directory(Path(config['paths']['final'])/"diagnostics/NAM/{sim_id}/{level}+{sim_id}+NAM.zar")
    # wildcard_constraints:
    #     sim_id = "([^_]*_){6}[^_]*"
    params:
        threads_per_worker=1,
        memory_limit="5GB",
        n_workers=12,
        mem='60GB',
        cpus_per_task=12,
        time=170
    script:
        f"{home}workflow/scripts/concatenation_diag.py"

rule diag_improved_et_heatmap:
    input:
       sim=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS_diag-sim-meas+{sim_id}+{region}.zarr",
       scen=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/DIAGNOSTICS_diag-scen-meas+{sim_id}+{region}.zarr"
    output:
        diag_heatmap=temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOCTICS_diag-heatmap+{sim_id}+{region}.zarr")),
        diag_improved= temp(directory(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOCTICS_diag-improved+{sim_id}+{region}.zarr"))
    # wildcard_constraints:
    #     region=r"[a-zA-Z]+_[a-zA-Z]+",
    #     sim_id= "([^_]*_){6}[^_]*"
    # params:
    #     threads_per_worker= lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
    #     memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
    # resources:
    #     mem='60GB',
    #     n_workers=3,
    #     cpus_per_task=12
    # resources:
    #     mem_mb=60000
    params:
        threads_per_worker=4,
        memory_limit="30GB",
        n_workers=3,
        mem='60GB',
        cpus_per_task=12,
        time=170
    script:
        f"{home}workflow/scripts/diag_improved_et_heatmap.py"



