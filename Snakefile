from snakemake.utils import min_version
from pathlib import Path
##### set minimum snakemake version #####
min_version("8.12.0")

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

##### target rules #####

rule all:
    input:
        # expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved_{sim_id}_{dom_name}.zarr", sim_id=sim_id_name,dom_name=dom),
        # expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOCTICS_diag-heatmap_{sim_id}_{region}.zarr", sim_id=sim_id_name,region=region_name),
        # expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOCTICS_diag-improved_{sim_id}_{region}.zarr", sim_id=sim_id_name, region=region_name),
        # expand(Path(config['paths']['final'])/"diagnostics/NAM/{sim_id}/{level}_{sim_id}_NAM.zar", sim_id=sim_id_name,level=level_name),
        # expand(Path(config['paths']['final']) / "checks/NAM/{sim_id}_NAM_checks.zarr", sim_id=sim_id_name),
        # Path(config['paths']['final']) / "diagnostics/NAM/ECMWF-ERA5-Land_NAM/diag-ref-prop_ECMWF-ERA5-Land_NAM.zar"
        # expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_extracted.zarr", sim_id=sim_id_name,region=region_name)
        # expand(Path(config['paths']['final'])/"reference/ref_{region}_default.zarr", region=region_name)
        expand(Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr", region=region_name),
        expand(Path(config['paths']['final'])/"diagnostics/NAM/ECMWF-ERA5-Land_NAM/diag-ref-prop_ECMWF-ERA5-Land_NAM.zar"),
        expand(Path(config['paths']['final']) / "reference/ref_{region}_360_day.zarr", region=region_name)
'''
snakemake \
    --jobs 10 \
    --default-resource mem_mb=100000 \
    --cluster '
      sbatch \
        --partition c-frigon \
        --account ctb-frigon \
        --constraint genoa \
        --cpus-per-task 6\
        --time 1-0:0:0 \
        --output output/{rule}_%j.out'
'''



'''
snakemake \
    --jobs 10 \
    --cluster '
      sbatch \
        --mem 100G \
        --partition c-frigon \
        --account ctb-frigon \
        --constraint genoa \
        --cpus-per-task 6\
        --time 02:00:00 \
        --output output/{rule}_%j.out'
'''