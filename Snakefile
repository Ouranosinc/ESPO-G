#TODO: before next run, check final attrs and final destination (maybe put direct in staging)
#TODO: add hurs diags
#TODO: figure out naming and versioning of ESPO
from snakemake.utils import min_version
from pathlib import Path
import pandas as pd
import copy
import xscen as xs

min_version("8.12.0") #set minimum snakemake version

configfile: "config/config_general.yml"
configfile: "config/config_region.yml"
configfile: "config/paths.yml"

# choose the simulations to process
dict_sim_id = xs.search_data_catalogs(**copy.deepcopy(config['extraction']['simulation']['search_data_catalogs'],))
sim_ids= list(dict_sim_id.keys())

subregions = list(config["custom"]["regions"].keys())
ref_source = [config['extraction']['reference']['search_data_catalogs']['other_search_criteria']['source']]
level=['improvement', 'diag_sim_prop','diag_sim_meas','diag_scen_prop','diag_scen_meas']
# trick, use dom as wildcard so it can be defined in the config
domain=[config['custom']['full_region']['name']]
tmpdir= Path(config['paths']['tmpdir'])
finaldir=Path(config['paths']['final'])

#TODO: optimize params

rule all:
    input:
        expand(finaldir/"checks/{dom}/{sim_id}+{dom}_checks.zarr.zip", sim_id=sim_ids, dom=domain),
        expand(finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_imp.zarr.zip",sim_id=sim_ids, dregion=diagregions, dom=domain)


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
        time="00:15:00",
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
          time="01:00:00",
     script:
          "workflow/scripts/rechunk.py"

rule train:
    input:
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
        noleap = finaldir/ "reference/split_regions/{dom}_{subregion}_noleap.zarr.zip", #TODO: for test adapt
        day360 = finaldir/ "reference/split_regions/{dom}_{subregion}_360_day.zarr.zip", #TODO: for test adapt
    output:
        temp(directory(tmpdir/"{sim_id}+{dom}+{subregion}+{var}+adjusted.zarr"))
    params:
        n_workers=3,
        mem='200GB',
        cpus_per_task=15,
        time="01:00:00",
    script:
        "workflow/scripts/adjust.py"

rule clean_up:
    input:
        expand(tmpdir/"{{sim_id}}+{{dom}}+{{subregion}}+{var}+adjusted.zarr",var=list(config['biasadjust']['variables'].keys()))
    output:
        temp(directory(tmpdir/"day+{sim_id}+{dom}+{subregion}+1950-2100.zarr"))
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=6,
        time="00:20:00",
    script:
        "workflow/scripts/clean_up.py"


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
         date_start=config['extraction']['simulation']['search_data_catalogs']['periods'][0], 
         date_end=config['extraction']['simulation']['search_data_catalogs']['periods'][1])))
    return str(os.path.dirname(os.path.dirname(path)))


#sim_id HAS to be in output, so can't use only params
#TODO: put right variables
rule concatenation_final:
    input: 
       final = expand(tmpdir/"day+{{sim_id}}+{{dom}}+{subregion}+1950-2100.zarr",  subregion=subregions)
    output: 
        pr=finaldir/"staging/{path}/pr/pr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip", 
        tasmax=finaldir/"staging/{path}/tasmax/tasmax_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip",
        tasmin=finaldir/"staging/{path}/tasmin/tasmin_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip",
        dtr=finaldir/"staging/{path}/dtr/dtr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip", 
        hurs=finaldir/"staging/{path}/hurs/hurs_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip", 
        hursTasmaz=finaldir/"staging/{path}/hursTasmax/hursTasmax_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip", 

    params:
        path=lambda wildcards: final_path(wildcards.sim_id),
        mem="60GB",
        time="01:00:00", 
        cpus_per_task=12,
    script:
        "workflow/scripts/concat.py"



rule health_checks:
    input:
        pr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/pr/pr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        tasmax=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmax/tasmax_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        tasmin=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmin/tasmin_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        dtr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/dtr/dtr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        hurs=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/hurs/hurs_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        hursTasmax=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/hursTasmax/hursTasmax_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),

    output:
        finaldir/"checks/{dom}/{sim_id}+{dom}_checks.zarr.zip"
    params:
        n_workers=8,
        mem='40GB',
        cpus_per_task=40,
        time="00:20:00",
    script:
        "workflow/scripts/health_check.py"

#try diag
rule diag_ref:
    input:
        ref=finaldir/ "reference/{dom}_default.zarr.zip"
    output: 
        prop=finaldir/"diagnostics/{dom}/{dregion}/prop_ref.zarr.zip"
    params:
        n_workers=6,
        mem="90GB",
        time="00:10:00", 
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
        scen_hurs=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/hurs/hurs_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_hursTasmax=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/hursTasmax/hursTasmax_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip"),
    output: 
        sim_prop=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_sim-prop.zarr.zip",
        sim_meas=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_sim-meas.zarr.zip",
        scen_prop=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_scen-prop.zarr.zip",
        scen_meas=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_scen-meas.zarr.zip",
        imp=finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_imp.zarr.zip",
    params:
        n_workers=2, 
        mem="100GB", 
        cpus_per_task=4,
        time="1:00:00", 
    script:
        "workflow/scripts/diag.py"
