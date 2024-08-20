from pathlib import Path

home=config["paths"]["home"]

rule adjust:
    input:
        train = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+{var}+training.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+regchunked.zarr",
    output:
        temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+{var}+adjusted.zarr"))
    # wildcard_constraints:
    #     region = r"[a-zA-Z]+_[a-zA-Z]+",
    #     sim_id="([^_]*_){6}[^_]*"
#    params:
#        threads_per_worker=lambda wildcards, resources: int(resources.cpus_per_task / resources.n_workers),
#        memory_limit=lambda wildcards, resources: int(resources.mem.rstrip("GB")) / resources.n_workers
#    resources:
#         mem='60GB',
#         n_workers=5,
#         cpus_per_task=15,
    # resources:
    #     mem_mb=100000,
    params:
        threads_per_worker=5,
        memory_limit="33GB",
        n_workers=3,
        mem='100GB',
        cpus_per_task=15,
        time=170
    script:
        f"{home}workflow/scripts/adjust.py"

