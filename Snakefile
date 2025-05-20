#TODO: before next run, check final attrs and final destination (maybe put direct in staging)

from snakemake.utils import min_version
from pathlib import Path

min_version("8.12.0") #set minimum snakemake version

configfile: "config/config-general.yml"
configfile: "config/config-region.yml"
configfile: "config/paths.yml"

include: "workflow/rules/common.smk"
include: "workflow/rules/Makeref.smk"
include: "workflow/rules/off_diag.smk"

#sim_ids = wildcards_sim_id()
sim_ids=['CMIP6_ScenarioMIP_NOAA-GFDL_GFDL-ESM4_ssp585_r1i1p1f1_global']#TODO: test
regions = list(config["custom"]["regions"].keys())
#diag_domain = config['off-diag']['domains'].keys()
diag_domain=['Ute']#TODO: test
ref_source = [config['extraction']['reference']['search_data_catalogs']['other_search_criteria']['source']]
level=['improvement', 'diag_sim_prop','diag_sim_meas','diag_scen_prop','diag_scen_meas']
# trick, use dom as wildcard so it can be defined in the config
domain=[config['custom']['full_region']['name']]
tmpdir= Path(config['paths']['tmpdir'])
finaldir=Path(config['paths']['final'])

rule all:
    input:
        expand(finaldir/"checks/{dom}/{sim_id}+{dom}_checks.zarr", sim_id=sim_ids, dom=domain),
        #expand(finaldir/"diagnostics/{diag_domain}/{sim_id}+{dom}+{diag_domain}+{level}.zarr.zip", diag_domain=diag_domain, sim_id=sim_ids, level=level, dom=domain),
        #expand(finaldir/"diagnostics/{diag_domain}/{ref_source}+{dom}+{diag_domain}+diag_ref_prop.zarr.zip", diag_domain=diag_domain, ref_source=ref_source, dom=domain),
#TODO: final path like MBCn and fix diag

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
          noleap = expand(finaldir/"reference/{ref_source}+{{dom}}+{{region}}+noleap.zarr",ref_source=ref_source)[0],
          extract = tmpdir/"{sim_id}+{dom}+extracted.zarr"
     output:
          temp(directory(tmpdir/"{sim_id}+{dom}+{region}+regridded.zarr"))
     params:
          n_workers=3,
          mem='48GB',
          cpus_per_task=9,
          time="00:20:00",
     script:
          "workflow/scripts/regrid.py"

rule rechunk:
     input:
          tmpdir/"{sim_id}+{dom}+{region}+regridded.zarr"
     output:
          temp(directory(tmpdir/"{sim_id}+{dom}+{region}+regchunked.zarr"))
     params:
          n_workers=2,
          mem='50GB',
          cpus_per_task=10,
          time="00:20:00",
     script:
          "workflow/scripts/rechunk.py"

rule train:
    input:
        noleap = expand(finaldir/"reference/{ref_source}+{{dom}}+{{region}}+noleap.zarr",ref_source=ref_source)[0],
        day360 = expand(finaldir/"reference/{ref_source}+{{dom}}+{{region}}+360_day.zarr",ref_source=ref_source)[0],
        rechunk = tmpdir/"{sim_id}+{dom}+{region}+regchunked.zarr",
    output:
        temp(directory(tmpdir/"{sim_id}+{dom}+{region}+{var}+training.zarr"))
    params:
        n_workers=3,
        mem='100GB',
        cpus_per_task=12,
        time="01:00:00",
    script:
        "workflow/scripts/train.py"

rule adjust:
    input:
        train = tmpdir/"{sim_id}+{dom}+{region}+{var}+training.zarr",
        rechunk = tmpdir/"{sim_id}+{dom}+{region}+regchunked.zarr",
        noleap = expand(finaldir/"reference/{ref_source}+{{dom}}+{{region}}+noleap.zarr",ref_source=ref_source)[0], #TODO: test adapt
        day360 = expand(finaldir/"reference/{ref_source}+{{dom}}+{{region}}+360_day.zarr",ref_source=ref_source)[0], #TODO: test adapt
    output:
        temp(directory(tmpdir/"{sim_id}+{dom}+{region}+{var}+adjusted.zarr"))
    params:
        n_workers=3,
        mem='100GB',
        cpus_per_task=15,
        time="06:00:00",
    script:
        "workflow/scripts/adjust.py"

rule clean_up:
    input:
        expand(tmpdir/"{{sim_id}}+{{dom}}+{{region}}+{var}+adjusted.zarr",var=["pr", "dtr", "tasmax"])
    output:
        temp(directory(tmpdir/"{sim_id}+{dom}+{region}+cleaned_up.zarr"))
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=6,
        time="00:20:00",
    script:
        "workflow/scripts/clean_up.py"

rule final_zarr:
    input:
        tmpdir/"{sim_id}+{dom}+{region}+cleaned_up.zarr",
    output:
        temp(directory(tmpdir/"day+{sim_id}+{dom}+{region}+1950-2100.zarr"))
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time="00:20:00",
    script:
        "workflow/scripts/final_zarr.py"

#TODO: future improvement like mbcn
# def final_path(id):
#     path='test'
#     path= xs.build_path(
#         data=pd.Series(
#             dict(zip(['mip_era','activity','institution','source', 'experiment','member'],id.split('_'))
#      )|dict(
#         domain=config['full_region']['name'],
#         format='zarr.zip',
#          variable='foo',
#          type='simulation',
#          processing_level='biasadjusted',
#          bias_adjust_project=config['biasadjust']['variables']['tasmax']['adjusting_args']['bias_adjust_project'],
#          bias_adjust_institution=config['biasadjust']['variables']['tasmax']['adjusting_args']['bias_adjust_institution'],
#          version=config['clean_up']['xscen_clean_up']['add_attrs']['global']['cat:version'],
#          frequency='day',
#          xrfreq='D',
#          date_start=config['biasadjust_mbcn']['adjust']['periods'][0], 
#          date_end=config['biasadjust_mbcn']['adjust']['periods'][1])))
#     return str(os.path.dirname(os.path.dirname(path)))


# #sim_id HAS to be in output, so can't use only params
# rule concatenation_final:
#     input: 
#        final = expand(tmpdir/"day+{{sim_id}}+{{dom}}+{region}+1950-2100.zarr",  region=regions)
#     output: 
#         pr=finaldir/"staging/{path}/pr/pr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip", 
#         tasmax=finaldir/"staging/{path}/tasmax/tasmax_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip",
#         tasmin=finaldir/"staging/{path}/tasmin/tasmin_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip",
#         #dtr=finaldir/"staging/{path}/dtr/dtr_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip", 
#         #tas=finaldir/"staging/{path}/tas/tas_day_DQM_{sim_id}_{dom}_1951-2100.zarr.zip",
#     params:
#         path=lambda wildcards: final_path(wildcards.sim_id),
#         mem="60GB",
#         time="00:20:00", 
#         cpus_per_task=12,
#     script:
#         "workflow/scripts/concat.py" #TODO: fix script

rule concatenation_final:
    input:
       final = expand(tmpdir/"day+{{sim_id}}+{{dom}}+{region}+1950-2100.zarr",  region=regions)
    output:
        tmp = temp(directory(tmpdir/"day+{sim_id}+{dom}_1950-2100.zarr")),
        final = finaldir/"final/{dom}/day+{sim_id}+{dom}_1950-2100.zarr.zip"
    params:
        n_workers=12,
        mem='60GB',
        cpus_per_task=12,
        time="00:20:00",
    script:
        "workflow/scripts/concat.py"


rule health_checks:
    input:
       finaldir/"final/{dom}/day+{sim_id}+{dom}_1950-2100.zarr.zip"
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
        final=tmpdir/"day+{sim_id}+{dom}+{region}+1950-2100.zarr",
        regchunked=tmpdir/"{sim_id}+{dom}+{region}+regchunked.zarr",
    output:
        final=finaldir/"SPLIT/{region}/day+{sim_id}+{dom}+{region}+1950-2100.zarr.zip",
        regchunked=finaldir/"regridded/day+{sim_id}+{dom}+{region}+regchunked.zarr.zip",
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
        time="00:20:00",
    script:
        "workflow/scripts/move.py"