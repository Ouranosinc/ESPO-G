from snakemake.utils import min_version
from pathlib import Path
##### set minimum snakemake version #####
min_version("8.8.0")

##### setup report #####
configfile: "config/config.yaml"

include: "workflow/rules/common.smk"
include: "workflow/rules/Makeref.smk"
include: "workflow/rules/extract.smk"
include: "workflow/rules/regrid.smk"
include: "workflow/rules/rechunk.smk"
include: "workflow/rules/train.smk"
include: "workflow/rules/adjust.smk"
include: "workflow/rules/clean_up.smk"
include: "workflow/rules/final_zarr.smk"
include: "workflow/rules/DIAGNOSTICS.smk"
include: "workflow/rules/health_check.smk"
include: "workflow/rules/official_diagnostics.smk"
include: "workflow/rules/indicators.smk"
include: "workflow/rules/climatological_mean.smk"
include: "workflow/rules/deltas.smk"

region_name = list(config["custom"]["regions"].keys())
sim_id_name = wildcards_sim_id()
var_name=config['biasadjust']['variables'].keys()
level_name=['diag-sim-meas', 'diag-scen-meas', 'diag-sim-prop', 'diag-scen-prop']
dom = config['off-diag']['domains'].keys()
processing_level = ['diag-sim-meas', 'diag-scen-meas']
indname_name = indname_name_func()
freqs = iter_freq()
delta_task = ["abs-delta","per-delta"]
process_level_name = config['ensemble']['processing_levels']
variable_name = varible_name()
experiment_name = experiment_name()

##### target rules #####

rule all:
    input:
        expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/NAM_{process_level}_{variable}_{xrfreq}_{experiment}_ensemble.zarr",
                process_level=process_level_name,xrfreq=freqs,variable=variable_name,experiment=experiment_name)
