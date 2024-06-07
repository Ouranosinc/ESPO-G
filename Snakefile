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

region=list(config["custom"]["regions"].keys())

##### target rules #####
rule all:
    input:
        #inter_region(), # pas besoin
        expand(Path(config['paths']['final'])/"diagnostics/{region_name}/ECMW-ERA5-Land_NAM/diag-ref-prop_ECMW-ERA5-Land_NAM_{region_name}.zarr", region_name=region)
