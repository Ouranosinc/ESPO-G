from snakemake.utils import min_version

##### set minimum snakemake version #####
min_version("8.12.0")

configfile: "config/config.yaml"
##### setup report #####
report: "report/workflow.rst"

##### load rules #####
include: "rules/common.smk"
include: "rules/Makeref.smk"

##### target rules #####
rule all:
    input:
        inter_region()