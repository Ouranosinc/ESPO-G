from snakemake.utils import min_version
from pathlib import Path

##### set minimum snakemake version #####
min_version("8.11.6")

configfile: "config/config.yaml"
##### setup report #####
report: "workflow/report/workflow.rst"

##### load rules #####
include: "workflow/rules/common.smk"
include: "workflow/rules/Makeref.smk"
include: "workflow/rules/extract.smk"
include: "workflow/rules/regrid.smk"
include: "workflow/rules/train.smk"
include: "workflow/rules/adjust.smk"

region_name = list(config["custom"]["regions"].keys())
sim_id_name = wildcards_sim_id()

##### target rules #####
rule all:
    input:
       expand(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regridded.zarr", sim_id=sim_id_name, region=region_name)