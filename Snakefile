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
# include: "workflow/rules/train.smk"
# include: "workflow/rules/adjust.smk"
# include: "workflow/rules/clean_up.smk"
# include: "workflow/rules/final_zarr.smk"
# include: "workflow/rules/DIAGNOSTICS.smk"
# include: "workflow/rules/health_check.smk"
# include: "workflow/rules/official_diagnostics.smk"

region_name = list(config["custom"]["regions"].keys())
sim_id_name = wildcards_sim_id()
# var_name=config['biasadjust']['variables'].keys()
# level_name=['diag-sim-meas', 'diag-scen-meas', 'diag-sim-prop', 'diag-scen-prop']

##### target rules #####

rule all:
    input:
        # expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_{region}_{var}_training.zarr",sim_id=sim_id_name,region=region_name,var=var_name)
        # expand(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_{var}_adjusted.zarr",sim_id=sim_id_name,region=region_name,var=var_name)
        # expand(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_cleaned_up.zarr",sim_id=sim_id_name,region=region_name)
        # expand(Path(config['paths']['output_snakemake'])/"NAM_SPLIT/{region}/day_{sim_id}_{region}_1950-2100.zarr",sim_id=sim_id_name,region=region_name)
        # expand(Path(config['paths']['final'])/"diagnostics/NAM/{sim_id}/{level}_{sim_id}_NAM.zar",sim_id=sim_id_name,level=level_name)
        # expand(Path(config['paths']['final']) / "checks/NAM/{sim_id}_NAM_checks.zarr",sim_id=sim_id_name)
        expand(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}_{region}_regchunked.zarr",sim_id=sim_id_name,region=region_name)
