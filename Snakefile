from snakemake.utils import min_version
from pathlib import Path
##### set minimum snakemake version #####
min_version("8.8.0")


##### setup report #####
configfile: "config/config.yaml"


include: "workflow/rules/common.smk"
include: "workflow/rules/Makeref.smk"
include: "workflow/rules/extract.smk"

region_name = list(config["custom"]["regions"].keys())
sim_id_name = wildcards_sim_id()

##### target rules #####

rule all:
    input:
        expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_extracted.zarr",sim_id=sim_id_name,region=region_name)