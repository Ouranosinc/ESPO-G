from snakemake.utils import min_version
from pathlib import Path

##### set minimum snakemake version #####
min_version("8.12.0")

##### setup report #####
configfile: "config/config.yaml"

include: "workflow/rules/common.smk"
include: "workflow/rules/Makeref.smk"
# include: "workflow/rules/extract.smk"
# include: "workflow/rules/regrid.smk"
# include: "workflow/rules/rechunk.smk"
# include: "workflow/rules/train.smk"
# include: "workflow/rules/adjust.smk"
# include: "workflow/rules/clean_up.smk"
#include: "workflow/rules/final_zarr.smk"
include: "workflow/rules/DIAGNOSTICS.smk"
include: "workflow/rules/health_check.smk"
include: "workflow/rules/official_diagnostics.smk"

region_name = list(config["custom"]["regions"].keys())
sim_id_name = wildcards_sim_id()
var_name=config['biasadjust']['variables'].keys()
level_name=['diag-sim-meas', 'diag-scen-meas', 'diag-sim-prop', 'diag-scen-prop']
dom = config['off-diag']['domains'].keys()
processing_level = ['diag-sim-meas', 'diag-scen-meas']

##### target rules #####
rule all:
    input:
        expand(Path(config['paths']['final'])/"FINAL/NAM/day+{sim_id}+NAM_1950-2100.zarr",sim_id=sim_id_name)
        #expand(Path(config['paths']['final'])/"NAM_SPLIT/{region}/day+{sim_id}+{region}+1950-2100.zarr",sim_id=sim_id_name,region=region_name),
        # expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/diag-improved+{sim_id}+{dom_name}.zarr", sim_id=sim_id_name,dom_name=dom),
        # expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/DIAGNOCTICS_diag-improved+{sim_id}+{region}.zarr", sim_id=sim_id_name, region=region_name),
        # expand(Path(config['paths']['final'])/"diagnostics/NAM/{sim_id}/{level}+{sim_id}+NAM.zar", sim_id=sim_id_name,level=level_name),
        # expand(Path(config['paths']['final']) / "checks/NAM/{sim_id}+NAM_checks.zarr", sim_id=sim_id_name),
        # Path(config['paths']['final']) / "diagnostics/NAM/ECMWF-ERA5-Land_NAM/diag-ref-prop_ECMWF-ERA5-Land_NAM.zarr"



rule extract:
    output:
        temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+extracted.zarr"))
    params:
        #threads_per_worker=5,
        #memory_limit="25GB",
        n_workers=2,
        mem="50GB",
        cpus_per_task=10,
        time=170
    script:
        "workflow/scripts/extract.py"

rule regrid:
     input:
          noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
          extract = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+extracted.zarr"
     output:
          temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+regridded.zarr"))
     params:
          threads_per_worker=3,
          memory_limit="15GB",
          n_workers=3,
          mem='48GB',
          cpus_per_task=9,
          time=170
     script:
          "workflow/scripts/regrid.py"

rule rechunk:
     input:
          Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+regridded.zarr"
     output:
          temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+regchunked.zarr"))
     params:
          threads_per_worker=5,
          memory_limit="25GB",
          n_workers=2,
          mem='50GB',
          cpus_per_task=10,
          time=170
     script:
          "workflow/scripts/rechunk.py"

rule train:
    input:
        noleap = Path(config['paths']['final'])/"reference/ref_{region}_noleap.zarr",
        day360 = Path(config['paths']['final'])/"reference/ref_{region}_360_day.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+regchunked.zarr",
    output:
        temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+{var}+training.zarr"))
    params:
        threads_per_worker=4,
        memory_limit="33GB",
        n_workers=3,
        mem='100GB',
        cpus_per_task=12,
        time=170
    script:
        "workflow/scripts/train.py"

rule adjust:
    input:
        train = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+{var}+training.zarr",
        rechunk = Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+regchunked.zarr",
    output:
        temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+{var}+adjusted.zarr"))
    params:
        threads_per_worker=5,
        memory_limit="33GB",
        n_workers=3,
        mem='100GB',
        cpus_per_task=15,
        time=170
    script:
        "workflow/scripts/adjust.py"

rule clean_up:
    input:
        expand(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{{sim_id}}+{{region}}+{var}+adjusted.zarr",var=["pr", "dtr", "tasmax"])
    output:
        temp(directory(Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+cleaned_up.zarr"))
    params:
        threads_per_worker=3,
        memory_limit="25GB",
        n_workers=2,
        mem='50GB',
        cpus_per_task=6,
        time=170
    script:
        "workflow/scripts/clean_up.py"

rule final_zarr:
    input:
        clean_up=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+cleaned_up.zarr",
        regridded=Path(config['paths']['exec_workdir'])/"ESPO-G_workdir/{sim_id}+{region}+regchunked.zarr"
    output:
        directory(Path(config['paths']['final'])/"NAM_SPLIT/{region}/day+{sim_id}+{region}+1950-2100.zarr")
    params:
        threads_per_worker=5,
        memory_limit="25GB",
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time=170
    script:
        "workflow/scripts/final_zarr.py"

rule concatenation_final:
    input:
        final = expand(Path(config['paths']['final'])/"NAM_SPLIT/{region}/day+{{sim_id}}+{region}+1950-2100.zarr",  region=list(config["custom"]["regions"].keys()))
    output:
        directory(Path(config['paths']['final'])/"FINAL/NAM/day+{sim_id}+NAM_1950-2100.zarr")
    params:
        threads_per_worker=1,
        memory_limit="5GB",
        n_workers=12,
        mem='60GB',
        cpus_per_task=12,
        time=170
    script:
        "workflow/scripts/concatenation_final.py"
