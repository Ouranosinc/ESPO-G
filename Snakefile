""" Snakefile for ESPO workflow
# Instructions before lauching the workflow:
1. Make sure begining and end date in config match hardcoded filename
2. Choose the right configs
3. Put the right log file in simple
"""
from snakemake.utils import min_version
from pathlib import Path
import pandas as pd
import copy
import xscen as xs
import numpy as np

configfile: "config/config_ESPO.yml"
configfile: "config/paths_ESPO.yml"

# Choose the simulations, diag, ref and dom to process
dict_sim_id = xs.search_data_catalogs(**copy.deepcopy(config['extraction']['simulation']['search_data_catalogs'],))
sim_ids= list(dict_sim_id.keys())
print(sim_ids)
diagregions=[d for d in config['diagregion'].keys()] # for diags
level=['improvement', 'diag_sim_prop','diag_sim_meas','diag_scen_prop','diag_scen_meas']
domain=[config['full_region']['name']]
reference = list(config['extraction']['reference'].keys())

# Define utils for pooling 
def id2poollist(sim_id,):
    """
    Given a sim_id, return the list of sim_ids that should be included in the 
    training based on the pool it belongs to. 
    """


    RIPF_PATTERN=r'r\d+i\d+p\d+f\d+'
    ripf_match = re.search(RIPF_PATTERN, sim_id)
    ripf_span = ripf_match.span()

    # Build a regex from id: keep everything outside the r*i*p*f* part literal,
    # replace the r*i*p*f* part with the general pattern
    prefix = re.escape(sim_id[:ripf_span[0]])
    suffix = re.escape(sim_id[ripf_span[1]:])
    match_pattern = re.compile(f'^{prefix}{RIPF_PATTERN}{suffix}$')

    return [s for s in sim_ids if match_pattern.match(s)]

def id2poolname(sim_id,):
    """
    Given a sim_id, return the name of the pool it belongs to.
    """
    exp= re.search(r'(ssp[^_]+)', sim_id).group(1)
    if sim_id.count('_')==6: #GCM
        gcm = re.search(rf'_([^_]+)_{exp}', sim_id).group(1)
        match=f"ScenarioMIP_{gcm}_{exp}"
    elif sim_id.count('_')==8: #RCM
        gcm = re.search(r'_([^_]+)_(?=r\d+i\d+p\d+f\d+)', sim_id).group(1) 
        rcm = re.search(rf'_([^_]+)_{exp}', sim_id).group(1) 
        match=f"{rcm}_{gcm}_{exp}"
    else:
        raise(ValueError(f"sim_id {sim_id} not valid"))
    return  match

def poolname2poollist(poolname,):
    """
    Given a pool name, return the list of sim_ids that should be included in the pool.
    """
    #decompose pool name
    dpool_name= poolname.split('_')
    # of all pool_list, keep the one that have pool in the first (it could be any) element
    # put _ after poolname to avoid issue when a name is inside anothe (looking at you EC-Earth3-Veg)
    filtered = [list(l) for l in all_poollists if all([f"{pn}_" in l[0] for pn in dpool_name])]
    if len(filtered) != 1:
        raise ValueError(f"Pool {poolname} does not uniquely identify a list of simulations. Found: {filtered}")
    return filtered[0]
all_poollists=set([tuple(id2poollist(s)) for s in sim_ids])
print(all_poollists)

# Define subregions on which to split the computation
cat_ref = xs.search_data_catalogs(**config['extraction']['reference'][reference[0]]['search_data_catalogs'])
dc = cat_ref.popitem()[1]
dref = xs.extract_dataset(catalog=dc,
                            region=config['full_region'],
                            **config['extraction']['reference'][reference[0]]['extract_dataset']
                            )['D']
dref = xs.utils.stack_drop_nans(dref,dref.pr.isel(time=0, drop=True).notnull().compute(),)
num_of_regions= int(np.ceil(dref.sizes['loc']/config['subregions']['n']))
subregions=[f"sr-{i}" for i in range(num_of_regions)]

# Define paths
tmpdir= Path(config['paths']['tmpdir'])
finaldir=Path(config['paths']['final'])

rule all:
    input:
        expand(finaldir/"checks/{dom}/{sim_id}+{ref}+{dom}_checks.zarr.zip", sim_id=sim_ids, dom=domain, ref=reference),
        expand(finaldir/"checks/QC/{sim_id}+{ref}+{dom}+QC_checks.zarr.zip", sim_id=sim_ids, dom=domain, ref=reference),
        expand(finaldir/"preswap/dtrpreswap_day_ESPO6_v20_{ref}+{sim_id}_{dom}.zarr.zip", sim_id=sim_ids, dom=domain, ref=reference),
        # TODO: run diag in a second wave
        #expand(finaldir/"diagnostics/{ref}/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_imp.zarr.zip",sim_id=sim_ids, dregion=diagregions, dom=domain, ref=reference)

rule makeref:
    output:
        ref=finaldir/ "reference/{dom}_{ref}_fullregion.zarr.zip",
        ref_stack=finaldir/ "reference/{dom}_{ref}_stacked.zarr.zip",
    params:
        n_workers=6, 
        mem="90GB",
        time="00:45:00", 
        cpus_per_task=4, 
    script:
        "workflow/scripts/makeref.py"


rule refsubregion:
    input: 
        finaldir/ "reference/{dom}_{ref}_stacked.zarr.zip",
    output: 
        default=finaldir/ "reference/split_regions/{dom}_{ref}_{subregion}_default.zarr.zip",
    params:
        n_workers=2,
        mem="50GB",
        cpus_per_task=4,
        time="00:15:00",
    script: "workflow/scripts/ref-subregion.py"


rule extract:
    output:
        extract=temp(directory(tmpdir/"{pool}+{dom}+extracted.zarr"))
    params:
        n_workers=2,
        mem="400GB",
        cpus_per_task=10,
        time="01:00:00",
    script:
        "workflow/scripts/extract.py"


rule regrid:
     input:
          ref = finaldir/ "reference/split_regions/{dom}_{ref}_{subregion}_default.zarr.zip",
          extract = tmpdir/"{pool}+{dom}+extracted.zarr"
     output:
          temp(directory(tmpdir/"{pool}+{dom}+{ref}+{subregion}+regridded.zarr"))
     params:
          n_workers=2,
          cpus_per_task=6,
          mem='500GB',
          time="01:00:00",
     script:
          "workflow/scripts/regrid.py" 


rule rechunk:
     input:
          tmpdir/"{pool}+{dom}+{ref}+{subregion}+regridded.zarr"
     output:
          temp(directory(tmpdir/"{pool}+{dom}+{ref}+{subregion}+regchunked.zarr"))
     params:
          n_workers=2,
          cpus_per_task=10,
          mem='500GB',
          time="00:30:00",
     script:
          "workflow/scripts/rechunk.py"


rule train:
    input:
        ref = finaldir/ "reference/split_regions/{dom}_{ref}_{subregion}_default.zarr.zip",
        rechunk = tmpdir/"{pool}+{dom}+{ref}+{subregion}+regchunked.zarr"
    output:
        temp(directory(tmpdir/"{pool}+{dom}+{ref}+{subregion}+{var}+training.zarr"))
    params:
        n_workers=3,
        mem='300GB',
        cpus_per_task=12,
        time="01:00:00",
    script:
        "workflow/scripts/train.py"


rule adjust: 
    input:
        train = tmpdir/"{pool}+{dom}+{ref}+{subregion}+{var}+training.zarr",
        rechunk = tmpdir/"{pool}+{dom}+{ref}+{subregion}+regchunked.zarr",
    output:
        temp(directory(tmpdir/"{pool}+{dom}+{ref}+{subregion}+{var}+adjusted.zarr"))
    params:
        n_workers=5,
        cpus_per_task=15,
        mem='300GB', 
        time="00:30:00", 
    script:
       "workflow/scripts/adjust.py"


def final_path(id, ref):
    path='test'
    # facets from id 
    if 'CORDEX' in id:
        f= dict(zip(['mip_era','activity','driving_model','driving_member', 'institution','source','experiment', 'member', ''],id.split('_')))
    else:
        f= dict(zip(['mip_era','activity','institution','source', 'experiment','member'],id.split('_')))
    path= xs.build_path(
        data=pd.Series(
           f
     |dict(
        domain=config['full_region']['name'],
        format='zarr.zip',
         variable='foo',
         type='simulation',
         processing_level='biasadjusted',
         bias_adjust_project=config['biasadjust']['variables']['tasmax']['adjusting_args']['bias_adjust_project'],
         bias_adjust_institution=config['biasadjust']['variables']['tasmax']['adjusting_args']['bias_adjust_institution'],
         bias_adjust_reference=ref,
         version=config['clean_up']['xscen_clean_up']['tasmax']['add_attrs']['global']['version'].replace('.',''),
         frequency='day',
         xrfreq='D',
         date_start=config['extraction']['simulation']['search_data_catalogs']['periods'][0], 
         date_end=config['extraction']['simulation']['search_data_catalogs']['periods'][1])))
    return str(os.path.dirname(os.path.dirname(path)))


rule swap: 
    input:
        tasmin = tmpdir/"{pool}+{dom}+{ref}+{subregion}+tasmin+adjusted.zarr",
        tasmax = tmpdir/"{pool}+{dom}+{ref}+{subregion}+tasmax+adjusted.zarr",
    output:
        tasmin = temp(directory(tmpdir/"{pool}+{dom}+{ref}+{subregion}+tasmin+adjustedS.zarr")),
        tasmax = temp(directory(tmpdir/"{pool}+{dom}+{ref}+{subregion}+tasmax+adjustedS.zarr")),
        dtrpreswap = temp(directory(tmpdir/"preswap/{pool}+{dom}+{ref}+{subregion}+dtrpreswap.zarr")),
    params:
        n_workers=5,
        cpus_per_task=15,
        mem='300GB', 
        time="00:10:00", 
    script:
        "workflow/scripts/swap_temp.py"


rule rename_files: #to get to adjustedS like swap
    input:
        dtr = tmpdir/"{pool}+{dom}+{ref}+{subregion}+dtr+adjusted.zarr",
        pr = tmpdir/"{pool}+{dom}+{ref}+{subregion}+pr+adjusted.zarr",
    output:
        dtr = temp(directory(tmpdir/"{pool}+{dom}+{ref}+{subregion}+dtr+adjustedS.zarr")),
        pr = temp(directory(tmpdir/"{pool}+{dom}+{ref}+{subregion}+pr+adjustedS.zarr")),
    params:
        n_workers=5,
        cpus_per_task=15,
        mem='300GB', 
        time="00:05:00", 
    shell:
        "mv {input.dtr} {output.dtr} && mv {input.pr} {output.pr}"


rule concat_clean:
    input: 
        adjusted=lambda wildcards: expand(tmpdir/(f"{id2poolname(wildcards.sim_id)}"+"+{{dom}}+{{ref}}+{subregion}+{{var}}+adjustedS.zarr"),  subregion=subregions),
        extracted=lambda wildcards: tmpdir/(f"{id2poolname(wildcards.sim_id)}"+"+{dom}+extracted.zarr")
    output: 
        finaldir/"staging/{path}/{var}/{var}_day_ESPO6_v20_{ref}+{sim_id}_{dom}_1951-2100.zarr.zip", 
    params:
        path=lambda wildcards: final_path(wildcards.sim_id, wildcards.ref),
        mem="60GB",
        time="01:00:00", 
        cpus_per_task=12,
    script:
        "workflow/scripts/concat_clean_up.py"


rule concat_clean_preswap:
    input: 
        adjusted=lambda wildcards: expand(tmpdir/(f"preswap/{id2poolname(wildcards.sim_id)}"+"+{{dom}}+{{ref}}+{subregion}+dtrpreswap.zarr"),  subregion=subregions),
        extracted=lambda wildcards: tmpdir/(f"{id2poolname(wildcards.sim_id)}"+"+{dom}+extracted.zarr")
    output: 
        finaldir/"preswap/dtrpreswap_day_ESPO6_v20_{ref}+{sim_id}_{dom}.zarr.zip", 
    params:
        mem="60GB",
        time="01:00:00", 
        cpus_per_task=12,
    script:
        "workflow/scripts/concat_clean_up.py"


rule health_checks:
    input:
        pr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id,wildcards.ref)}"+"/pr/pr_day_ESPO6_v20_{ref}+{sim_id}_{dom}_1951-2100.zarr.zip"),
        tasmax=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id,wildcards.ref)}"+"/tasmax/tasmax_day_ESPO6_v20_{ref}+{sim_id}_{dom}_1951-2100.zarr.zip"),
        tasmin=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id,wildcards.ref)}"+"/tasmin/tasmin_day_ESPO6_v20_{ref}+{sim_id}_{dom}_1951-2100.zarr.zip"),
        dtr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id,wildcards.ref)}"+"/dtr/dtr_day_ESPO6_v20_{ref}+{sim_id}_{dom}_1951-2100.zarr.zip"),
    output:
        NAM=finaldir/"checks/{dom}/{sim_id}+{ref}+{dom}_checks.zarr.zip",
        QC=finaldir/"checks/QC/{sim_id}+{ref}+{dom}+QC_checks.zarr.zip"
    params:
        n_workers=8,
        mem='40GB',
        cpus_per_task=40,
        time="00:30:00",
    script:
        "workflow/scripts/health_check.py"


rule diag_ref:
    input:
        ref=finaldir/ "reference/{dom}_{ref}_fullregion.zarr.zip"
    output: 
        prop=finaldir/"diagnostics/{ref}/{dom}/{dregion}/ref-prop.zarr.zip"
    params:
        n_workers=6,
        mem="90GB",
        time="00:10:00", 
        cpus_per_task=4,
    script:
        "workflow/scripts/diag_ref.py"


rule diag:
    input:
        ref=finaldir/ "reference/{dom}_{ref}_fullregion.zarr.zip",
        ref_prop=finaldir/"diagnostics/{ref}/{dom}/{dregion}/ref-prop.zarr.zip",
        scen_pr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id,wildcards.ref)}"+"/pr/pr_day_ESPO6_v20_{ref}+{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_tasmax=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id,wildcards.ref)}"+"/tasmax/tasmax_day_ESPO6_v20_{ref}+{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_tasmin=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id,wildcards.ref)}"+"/tasmin/tasmin_day_ESPO6_v20_{ref}+{sim_id}_{dom}_1951-2100.zarr.zip"),
        scen_dtr=lambda wildcards: finaldir/(f"staging/{final_path(wildcards.sim_id,wildcards.ref)}"+"/dtr/dtr_day_ESPO6_v20_{ref}+{sim_id}_{dom}_1951-2100.zarr.zip"), 
    output: 
        sim_prop=finaldir/"diagnostics/{ref}/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_sim-prop.zarr.zip",
        sim_meas=finaldir/"diagnostics/{ref}/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_sim-meas.zarr.zip",
        scen_prop=finaldir/"diagnostics/{ref}/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_scen-prop.zarr.zip",
        scen_meas=finaldir/"diagnostics/{ref}/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_scen-meas.zarr.zip",
        imp=finaldir/"diagnostics/{ref}/{dom}/{dregion}/{sim_id}/{sim_id}_{dom}_{dregion}_imp.zarr.zip",
    params:
        n_workers=4, 
        cpus_per_task=4,
        mem="400GB", 
        time="9:00:00", 
    script:
        "workflow/scripts/diag.py"
