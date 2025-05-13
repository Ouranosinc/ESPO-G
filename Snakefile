from pathlib import Path
import xscen as xs
import pandas as pd
import os
import numpy as np

# Load configuration
#configfile: "config/config.yml"
configfile: "config/config_general.yml"
configfile: "config/config_region.yml"
configfile: "config/paths.yml"

# choose the simulations to process
dict_sim_id = xs.search_data_catalogs(**config['extraction']['simulation']['search_data_catalogs'],)
sim_ids= list(dict_sim_id.keys())
sim_ids=sim_ids[:5] 

# define subregions on which to split the computation based on n (size of each subregion) and the full region
if 'num_of_regions' not in config['subregions']:
    cat=xs.DataCatalog(config['extraction']['reference']['search_data_catalogs']['data_catalogs'][0])
    dref=cat.search(**config['extraction']['reference']['search_data_catalogs']['other_search_criteria']).to_dataset()
    dref=xs.spatial.subset(dref, **config['full_region'])
    dref = xs.utils.stack_drop_nans(dref,dref.pr.isel(time=0, drop=True).notnull().compute(),)
    num_of_regions= int(np.ceil(dref.sizes['loc']/config['subregions']['n']))
else:
    num_of_regions=config['subregions']['num_of_regions']
subregions=[f"sr-{i}" for i in range(num_of_regions)]

# trick, use dom as wildcard so it can be defined in the config
domain=[config['full_region']['name']]

# diagnostics regions
diagregions=[d for d in config['diagregion'].keys()]

#paths
wdir= Path(config['paths']['workdir'])
finaldir= Path(config['paths']['finaldir'])


rule all:
    input: 
        expand(finaldir/"health/{sim_id}_{dom}_health.zarr.zip",sim_id=sim_ids, dom=domain),
        expand(finaldir/"diagnostics/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_imp.zarr.zip",
        sim_id=sim_ids, dregion=diagregions, dom=domain)



rule makeref:
    output:
        ref=finaldir/ "reference/{dom}_default.zarr.zip",
        refstacked=finaldir/ "reference/{dom}_stacked_default.zarr.zip",
    params:
        #n_workers=2,# QC
        #mem="30GB", #QC
        #time="00:15:00", #QC
        n_workers=6, #NAM 
        mem="90GB", #NAM 
        time="00:45:00", #NAM 
        cpus_per_task=4, 
    script:
        "workflow/scripts/makeref.py"



rule refsubregion:
    input: 
        refstacked=finaldir/ "reference/{dom}_stacked_default.zarr.zip",
    output: 
        default=finaldir/ "reference/split_regions/{dom}_{subregion}_default.zarr.zip",
        noleap=finaldir/ "reference/split_regions/{dom}_{subregion}_noleap.zarr.zip",
        day360=finaldir/ "reference/split_regions/{dom}_{subregion}_360_day.zarr.zip",
    params:
        n_workers=2,
        mem="10GB",
        cpus_per_task=4,
        time="00:05:00",
    script: "workflow/scripts/ref-subregion.py"

rule extractregrid:
    input: 
        noleap=finaldir/ "reference/split_regions/{dom}_{subregion}_noleap.zarr.zip",
    output: temp(wdir/"{sim_id}_{dom}_{subregion}/{sim_id}_{subregion}_regridded.zarr.zip")
    params:
        mem="10GB", #2100
        #mem="20GB", # 2300
        cpus_per_task=1,
        time="00:20:00",
    script:
        "workflow/scripts/extract-regrid.py"

rule train:
    input:
        sim= wdir/"{sim_id}_{dom}_{subregion}/{sim_id}_{subregion}_regridded.zarr.zip",
        ref_noleap= finaldir/"reference/split_regions/{dom}_{subregion}_noleap.zarr.zip",
        ref_360_day= finaldir/"reference/split_regions/{dom}_{subregion}_360_day.zarr.zip",
    output: temp(wdir/"{sim_id}_{dom}_{subregion}/{sim_id}_{subregion}_training.zarr.zip"),
    params:
        n_workers=10,
        mem="30GB",
        cpus_per_task=12,
        time="01:00:00",
    script:
        "workflow/scripts/train.py"


rule adjust:
    input:
        sim= wdir/"{sim_id}_{dom}_{subregion}/{sim_id}_{subregion}_regridded.zarr.zip",
        ref_noleap= finaldir/"reference/split_regions/{dom}_{subregion}_noleap.zarr.zip",
        ref_360_day= finaldir/"reference/split_regions/{dom}_{subregion}_360_day.zarr.zip",
        train= wdir/"{sim_id}_{dom}_{subregion}/{sim_id}_{subregion}_training.zarr.zip",
    output: temp(wdir/"{sim_id}_{dom}_{subregion}/{sim_id}_{subregion}_adjusted.zarr.zip"),
    params:
        mem="80GB", # 2100
        time="12:00:00", # 2100
        #time="24:00:00", #2300
        #mem="160GB", # 2300
        cpus_per_task=1,
    script:
        "workflow/scripts/adjust.py"


def final_path(id):
    path='test'
    path= xs.build_path(
        data=pd.Series(
            dict(zip(['mip_era','activity','institution','source', 'experiment','member'],id.split('_'))
     )|dict(
        domain=config['full_region']['name'],
        format='zarr.zip',
         variable='foo',
         type='simulation',
         processing_level='biasadjusted',
         bias_adjust_project=config['biasadjust_mbcn']['attrs']['bias_adjust_project'],
         bias_adjust_institution=config['biasadjust_mbcn']['attrs']['bias_adjust_institution'],
         version=config['biasadjust_mbcn']['attrs']['version'],
         frequency='day',
         xrfreq='D',
         date_start=config['biasadjust_mbcn']['adjust']['periods'][0], 
         date_end=config['biasadjust_mbcn']['adjust']['periods'][1])))
    return str(os.path.dirname(os.path.dirname(path)))



#sim_id HAS to be in output, so can't use only params
rule concat_scen_clean:
    input: expand(wdir/"{{sim_id}}_{{dom}}_{subregion}/{{sim_id}}_{subregion}_adjusted.zarr.zip",subregion=subregions)
    output: 
        pr=finaldir/"staging/{path}/pr/pr_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip", 
        tasmax=finaldir/"staging/{path}/tasmax/tasmax_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip",
        tasmin=finaldir/"staging/{path}/tasmin/tasmin_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip",
        dtr=finaldir/"staging/{path}/dtr/dtr_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip", 
        tas=finaldir/"staging/{path}/tas/tas_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip",
    params:
        path=lambda wildcards: final_path(wildcards.sim_id),
        #mem="45GB", #QC
        #time="00:20:00", #QC
        mem="300GB", #NAM
        time="03:00:00", # NAM
        cpus_per_task=1,
    script:
        "workflow/scripts/concat_clean.py"


rule health:
    input:
        pr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/pr/pr_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
        tasmax=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmax/tasmax_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
        tasmin=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmin/tasmin_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
        dtr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/dtr/dtr_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
        tas=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tas/tas_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
    output: 
        finaldir/"health/{sim_id}_{dom}_health.zarr.zip"
    params:
        # n_workers=2,# QC
        # mem="20GB",# QC
        #time="00:10:00", # QC
        n_workers=6, #NAM
        mem="200GB", #NAM
        time="01:00:00", # NAM
        cpus_per_task=4,
    script:
        "workflow/scripts/health.py"

rule diag_ref:
    input:
        ref=finaldir/ "reference/{dom}_default.zarr.zip",
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
        scen_pr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/pr/pr_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_tasmax=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmax/tasmax_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_tasmin=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/tasmin/tasmin_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_dtr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id)}"+"/dtr/dtr_day_MBCn-EM_v10_{sim_id}_{dom}_1951-2100.zarr.zip"),
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


    

