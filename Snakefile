#TODO: before next run, check final attrs and final destination (maybe put direct in staging)

from snakemake.utils import min_version
from pathlib import Path

min_version("8.12.0") #set minimum snakemake version

configfile: "config/config.yml"
configfile: "config/paths.yml"

include: "workflow/rules/common.smk"
include: "workflow/rules/Makeref.smk"
include: "workflow/rules/off_diag.smk"

sim_id = wildcards_sim_id()
region = list(config["custom"]["regions"].keys())
diag_domain = config['off-diag']['domains'].keys()
ref_source = [config['extraction']['reference']['search_data_catalogs']['other_search_criteria']['source']]
level=['improvement', 'diag_sim_prop','diag_sim_meas','diag_scen_prop','diag_scen_meas']

tmpdir= Path(config['paths']['tmpdir'])
finaldir=Path(config['paths']['final'])

rule all:
    input:
        expand(finaldir/"checks/NAM/{sim_id}+NAM_checks.zarr", sim_id=sim_id),
        expand(finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+{level}.zarr.zip", diag_domain=diag_domain, sim_id=sim_id, level=level),
        expand(finaldir/"diagnostics/{diag_domain}/{ref_source}+{diag_domain}+diag_ref_prop.zarr.zip", diag_domain=diag_domain, ref_source=ref_source),


rule extract:
    output:
        temp(directory(tmpdir/"{sim_id}+NAM+extracted.zarr"))
    params:
        n_workers=2,
        mem="50GB",
        cpus_per_task=10,
    script:
        "workflow/scripts/extract.py"

rule regrid:
     input:
          noleap = expand(finaldir/"reference/{ref_source}+{{region}}+noleap.zarr",ref_source=ref_source)[0],
          extract = tmpdir/"{sim_id}+NAM+extracted.zarr"
     output:
          temp(directory(tmpdir/"{sim_id}+{region}+regridded.zarr"))
     params:
          n_workers=3,
          mem='48GB',
          cpus_per_task=9,
     script:
          "workflow/scripts/regrid.py"

rule rechunk:
     input:
          tmpdir/"{sim_id}+{region}+regridded.zarr"
     output:
          temp(directory(tmpdir/"{sim_id}+{region}+regchunked.zarr"))
     params:
          n_workers=2,
          mem='50GB',
          cpus_per_task=10,
     script:
          "workflow/scripts/rechunk.py"

rule train:
    input:
        noleap = expand(finaldir/"reference/{ref_source}+{{region}}+noleap.zarr",ref_source=ref_source)[0],
        day360 = expand(finaldir/"reference/{ref_source}+{{region}}+360_day.zarr",ref_source=ref_source)[0],
        rechunk = tmpdir/"{sim_id}+{region}+regchunked.zarr",
    output:
        temp(directory(tmpdir/"{sim_id}+{region}+{var}+training.zarr"))
    params:
        n_workers=3,
        mem='100GB',
        cpus_per_task=12,
    script:
        "workflow/scripts/train.py"

rule adjust:
    input:
        train = tmpdir/"{sim_id}+{region}+{var}+training.zarr",
        rechunk = tmpdir/"{sim_id}+{region}+regchunked.zarr",
    output:
        temp(directory(tmpdir/"{sim_id}+{region}+{var}+adjusted.zarr"))
    params:
        n_workers=3,
        mem='100GB',
        cpus_per_task=15,
    script:
        "workflow/scripts/adjust.py"

rule clean_up:
    input:
        expand(tmpdir/"{{sim_id}}+{{region}}+{var}+adjusted.zarr",var=["pr", "dtr", "tasmax"])
    output:
        temp(directory(tmpdir/"{sim_id}+{region}+cleaned_up.zarr"))
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=6,
    script:
        "workflow/scripts/clean_up.py"

rule final_zarr:
    input:
        tmpdir/"{sim_id}+{region}+cleaned_up.zarr",
    output:
        temp(directory(tmpdir/"day+{sim_id}+{region}+1950-2100.zarr"))
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
    script:
        "workflow/scripts/final_zarr.py"

# need different move bc wilcards have to be the same in a room
rule move:
    input:
        final=tmpdir/"day+{sim_id}+{region}+1950-2100.zarr",
        regchunked=tmpdir/"{sim_id}+{region}+regchunked.zarr",
    output:
        final=finaldir/"NAM_SPLIT/{region}/day+{sim_id}+{region}+1950-2100.zarr.zip",
        regchunked=finaldir/"regridded/day+{sim_id}+{region}+regchunked.zarr.zip",
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
    script:
        "workflow/scripts/move.py"



rule concatenation_final:
    input:
        final = expand(tmpdir/"day+{{sim_id}}+{region}+1950-2100.zarr",  region=region)
    output:
        tmp = temp(directory(tmpdir/"day+{sim_id}+NAM+1950-2100.zarr")),
        final = finaldir/"final/NAM/day+{sim_id}+NAM_1950-2100.zarr.zip"
    params:
        n_workers=12,
        mem='60GB',
        cpus_per_task=12,
    script:
        "workflow/scripts/concat.py"


rule health_checks:
    input:
        finaldir/"final/NAM/day+{sim_id}+NAM_1950-2100.zarr.zip"
    output:
        directory(finaldir/"checks/NAM/{sim_id}+NAM_checks.zarr")
    params:
        n_workers=8,
        mem='40GB',
        cpus_per_task=40,
    script:
        "workflow/scripts/health_check.py"