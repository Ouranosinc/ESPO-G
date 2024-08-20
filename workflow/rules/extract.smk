from pathlib import Path

home=config["paths"]["home"]

rule extract:
    #input:
    #    script=f"{home}workflow/scripts/extract.py"
    output:
        temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+extracted.zarr"))
    # wildcard_constraints:
    #     region = r"[a-zA-Z]+_[a-zA-Z]+",
    #     sim_id="([^_]*_){6}[^_]*"
    # resources:
    #     mem_mb=50000
    params:
        threads_per_worker=5,
        memory_limit="25GB",
        n_workers=2,
        mem="50GB",
        cpus_per_task=10,
        time=170
    script:
        f"{home}workflow/scripts/extract.py"