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

region=list(config["custom"]["regions"].keys())

##### target rules #####
rule all:
    input:
       "/exec/ocisse/ESPO-G6-stage/ESPO-G_workdir/NAM_south_nodup_regridded.zarr"
       "/exec/ocisse/ESPO-G6-stage/ESPO-G_workdir/NAM_middle_nodup_regridded.zarr"
       "/exec/ocisse/ESPO-G6-stage/ESPO-G_workdir/NAM_north_nodup_regridded.zarr"