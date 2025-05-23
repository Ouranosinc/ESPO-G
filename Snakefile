#TODO: before next run, check final attrs and final destination (maybe put direct in staging)

from snakemake.utils import min_version
from pathlib import Path
import pandas as pd

min_version("8.12.0") #set minimum snakemake version

configfile: "config/config-general.yml"
configfile: "config/config-region.yml"
configfile: "config/paths.yml"

include: "workflow/rules/common.smk"
include: "workflow/rules/Makeref.smk"
include: "workflow/rules/off_diag.smk"

#sim_ids = wildcards_sim_id()
sim_ids=['CMIP6_ScenarioMIP_NOAA-GFDL_GFDL-ESM4_ssp585_r1i1p1f1_global']#TODO: test
subregions = list(config["custom"]["regions"].keys())
#diag_domain = config['off-diag']['domains'].keys()
diagregions=['Ute']#TODO: test
ref_source = [config['extraction']['reference']['search_data_catalogs']['other_search_criteria']['source']]
level=['improvement', 'diag_sim_prop','diag_sim_meas','diag_scen_prop','diag_scen_meas']
# trick, use dom as wildcard so it can be defined in the config
domain=[config['custom']['full_region']['name']]
tmpdir= Path(config['paths']['tmpdir'])
finaldir=Path(config['paths']['final'])

#TODO: more zip
#TODO: clean config
#TODO: optimize params

rule all:
    input:
        expand(finaldir/"checks/{dom}/{sim_id}+{dom}_checks.zarr", sim_id=sim_ids, dom=domain),
        #expand(finaldir/"diagnostics/{diag_domain}/{sim_id}+{dom}+{diag_domain}+{level}.zarr.zip", diag_domain=diag_domain, sim_id=sim_ids, level=level, dom=domain),
        #expand(finaldir/"diagnostics/{diag_domain}/{ref_source}+{dom}+{diag_domain}+diag_ref_prop.zarr.zip", diag_domain=diag_domain, ref_source=ref_source, dom=domain),
        expand(finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_imp.zarr.zip",sim_id=sim_ids, dregion=diagregions, dom=domain)
#TODO: final path like MBCn and fix diag


rule makeref:
    output:
        ref=finaldir/ "reference/{dom}_default.zarr.zip",
    params:
        n_workers=6, 
        mem="90GB",
        time="00:45:00", 
        cpus_per_task=4, 
    script:
        "workflow/scripts/makeref.py"



rule refsubregion:
    input: 
        finaldir/ "reference/{dom}_default.zarr.zip",
    output: 
        default=finaldir/ "reference/split_regions/{dom}_{subregion}_default.zarr.zip",
        noleap=finaldir/ "reference/split_regions/{dom}_{subregion}_noleap.zarr.zip",
        day360=finaldir/ "reference/split_regions/{dom}_{subregion}_360_day.zarr.zip",
    params:
        n_workers=2,
        mem="50GB",
        cpus_per_task=4,
        time="00:30:00",
    script: "workflow/scripts/ref-subregion.py"


rule extract:
    output:
        temp(directory(tmpdir/"{sim_id}+{dom}+extracted.zarr"))
    params:
        n_workers=2,
        mem="50GB",
        cpus_per_task=10,
        time="00:20:00",
    script:
        "workflow/scripts/extract.py"

rule regrid:
     input:
          #noleap = expand(finaldir/"reference/{ref_source}+{{dom}}+{{subregion}}+noleap.zarr.zip",ref_source=ref_source)[0],
          noleap = finaldir/ "reference/split_regions/{dom}_{subregion}_noleap.zarr.zip",
          extract = tmpdir/"{sim_id}+{dom}+extracted.zarr"
     output:
          temp(directory(tmpdir/"{sim_id}+{dom}+{subregion}+regridded.zarr"))
     params:
          n_workers=3,
          mem='48GB',
          cpus_per_task=9,
          time="00:20:00",
     script:
          "workflow/scripts/regrid.py"

rule rechunk:
     input:
          tmpdir/"{sim_id}+{dom}+{subregion}+regridded.zarr"
     output:
          temp(directory(tmpdir/"{sim_id}+{dom}+{subregion}+regchunked.zarr"))
     params:
          n_workers=2,
          mem='50GB',
          cpus_per_task=10,
          time="02:00:00",
     script:
          "workflow/scripts/rechunk.py"

rule train:
    input:
        #noleap = expand(finaldir/"reference/{ref_source}+{{dom}}+{{subregion}}+noleap.zarr.zip",ref_source=ref_source)[0],
        #day360 = expand(finaldir/"reference/{ref_source}+{{dom}}+{{subregion}}+360_day.zarr.zip",ref_source=ref_source)[0],
        noleap = finaldir/ "reference/split_regions/{dom}_{subregion}_noleap.zarr.zip",
        day360 = finaldir/ "reference/split_regions/{dom}_{subregion}_360_day.zarr.zip",
        rechunk = tmpdir/"{sim_id}+{dom}+{subregion}+regchunked.zarr",
    output:
        temp(directory(tmpdir/"{sim_id}+{dom}+{subregion}+{var}+training.zarr"))
    params:
        n_workers=3,
        mem='100GB',
        cpus_per_task=12,
        time="02:00:00",
    script:
        "workflow/scripts/train.py"

rule adjust:
    input:
        train = tmpdir/"{sim_id}+{dom}+{subregion}+{var}+training.zarr",
        rechunk = tmpdir/"{sim_id}+{dom}+{subregion}+regchunked.zarr",
        #noleap = expand(finaldir/"reference/{ref_source}+{{dom}}+{{subregion}}+noleap.zarr.zip",ref_source=ref_source)[0], #TODO: test adapt
        #day360 = expand(finaldir/"reference/{ref_source}+{{dom}}+{{subregion}}+360_day.zarr.zip",ref_source=ref_source)[0], #TODO: test adapt
        noleap = finaldir/ "reference/split_regions/{dom}_{subregion}_noleap.zarr.zip", #TODO: test adapt
        day360 = finaldir/ "reference/split_regions/{dom}_{subregion}_360_day.zarr.zip", #TODO: test adapt
    output:
        temp(directory(tmpdir/"{sim_id}+{dom}+{subregion}+{var}+adjusted.zarr"))
    params:
        n_workers=3,
        mem='200GB',
        cpus_per_task=15,
        time="06:00:00",
    script:
        "workflow/scripts/adjust.py"

rule clean_up:
    input:
        expand(tmpdir/"{{sim_id}}+{{dom}}+{{subregion}}+{var}+adjusted.zarr",var=["pr", "dtr", "tasmax"])
    output:
        temp(directory(tmpdir/"{sim_id}+{dom}+{subregion}+cleaned_up.zarr"))
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=6,
        time="00:20:00",
    script:
        "workflow/scripts/clean_up.py"

rule final_zarr:
    input:
        tmpdir/"{sim_id}+{dom}+{subregion}+cleaned_up.zarr",
    output:
        temp(directory(tmpdir/"day+{sim_id}+{dom}+{subregion}+1950-2100.zarr"))
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time="01:00:00",
    script:
        "workflow/scripts/final_zarr.py"

#TODO: future improvement like mbcn
def final_path(id):
    path='test'
    path= xs.build_path(
        data=pd.Series(
            dict(zip(['mip_era','activity','institution','source', 'experiment','member'],id.split('_'))
     )|dict(
        domain=config['custom']['full_region']['name'],
        format='zarr.zip',
         variable='foo',
         type='simulation',
         processing_level='biasadjusted',
         bias_adjust_project=config['biasadjust']['variables']['tasmax']['adjusting_args']['bias_adjust_project'],
         bias_adjust_institution=config['biasadjust']['variables']['tasmax']['adjusting_args']['bias_adjust_institution'],
         version=config['clean_up']['xscen_clean_up']['add_attrs']['global']['cat:version'],
         frequency='day',
         xrfreq='D',
         date_start=config['custom']['sim_period'][0], 
         date_end=config['custom']['sim_period'][1])))
    return str(os.path.dirname(os.path.dirname(path)))


#sim_id HAS to be in output, so can't use only params
rule concatenation_final:
    input: 
       final = expand(tmpdir/"day+{{sim_id}}+{{dom}}+{subregion}+1950-2100.zarr",  subregion=subregions)
    output: 
        pr=finaldir/"staging/{path}/pr/pr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip", 
        tasmax=finaldir/"staging/{path}/tasmax/tasmax_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip",
        tasmin=finaldir/"staging/{path}/tasmin/tasmin_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip",
        dtr=finaldir/"staging/{path}/dtr/dtr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip", 
        #tas=finaldir/"staging/{path}/tas/tas_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip",
    params:
        path=lambda wildcards: final_path(wildcards.sim_id),
        mem="60GB",
        time="01:00:00", 
        cpus_per_task=12,
    script:
        "workflow/scripts/concat.py" #TODO: fix script

# rule concatenation_final:
#     input:
#        final = expand(tmpdir/"day+{{sim_id}}+{{dom}}+{subregion}+1950-2100.zarr",  region=regions)
#     output:
#         tmp = temp(directory(tmpdir/"day+{sim_id}+{dom}_1950-2100.zarr")),
#         final = finaldir/"final/{dom}/day+{sim_id}+{dom}_1950-2100.zarr.zip"
#     params:
#         n_workers=12,
#         mem='60GB',
#         cpus_per_task=12,
#         time="00:20:00",
#     script:
#         "workflow/scripts/concat.py"


rule health_checks:
    input:
       #finaldir/"final/{dom}/day+{sim_id}+{dom}_1950-2100.zarr.zip"
        pr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/pr/pr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        tasmax=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmax/tasmax_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        tasmin=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmin/tasmin_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        dtr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/dtr/dtr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        #tas=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tas/tas_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
    output:
        directory(finaldir/"checks/{dom}/{sim_id}+{dom}_checks.zarr")
    params:
        n_workers=8,
        mem='40GB',
        cpus_per_task=40,
        time="00:20:00",
    script:
        "workflow/scripts/health_check.py"

# # need different move bc wilcards have to be the same in a room
rule move:
    input:
        final=tmpdir/"day+{sim_id}+{dom}+{subregion}+1950-2100.zarr",
        regchunked=tmpdir/"{sim_id}+{dom}+{subregion}+regchunked.zarr",
    output:
        final=finaldir/"SPLIT/{subregion}/day+{sim_id}+{dom}+{subregion}+1950-2100.zarr.zip",
        regchunked=finaldir/"regridded/day+{sim_id}+{dom}+{subregion}+regchunked.zarr.zip",
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time="00:20:00",
    script:
        "workflow/scripts/move.py"


#try diag
rule diag_ref:
    input:
        ref=finaldir/ "reference/{dom}_default.zarr.zip"
    output: 
        prop=finaldir/"diagnostics/{dom}/{dregion}/prop_ref.zarr.zip"
    params:
        #n_workers=2,# QC
        #mem="30GB", #QC
        #time="00:15:00", #QC
        n_workers=6,
        mem="90GB",
        time="01:00:00", #NAM 
        cpus_per_task=4,
    script:
        "workflow/scripts/diag_ref.py"


rule diag:
    input:
        ref=finaldir/ "reference/{dom}_default.zarr.zip",
        ref_prop=finaldir/"diagnostics/{dom}/{dregion}/prop_ref.zarr.zip",
        scen_pr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/pr/pr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_tasmax=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmax/tasmax_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_tasmin=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmin/tasmin_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_dtr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/dtr/dtr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
    output: 
        sim_prop=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_sim-prop.zarr.zip",
        sim_meas=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_sim-meas.zarr.zip",
        scen_prop=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_scen-prop.zarr.zip",
        scen_meas=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_scen-meas.zarr.zip",
        imp=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_imp.zarr.zip",
    params:
        #n_workers=2,#QC
        #mem="50GB", #QC
        #time="01:00:00", #QC
        n_workers=2, #NAM
        mem="100GB", #NAM
        cpus_per_task=4,
        time="2:00:00", # NAM
    script:
        "workflow/scripts/diag.py"
