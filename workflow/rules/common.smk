import xscen as xs
import xarray as xr
from pathlib import Path

import zarr


# def wildcards_sim_id():
#     cat_sim = xs.search_data_catalogs(
#         **config['extraction']['simulation']['search_data_catalogs'])
#     sim_id = list(cat_sim.keys())
#     return sim_id

def wildcards_sim_id():
    cat_sim = xs.search_data_catalogs(
         **{'data_catalogs': ['/tank/scenario/catalogues/simulation.json'], 'variables_and_freqs': {'tasmax': 'D', 'tasmin': 'D', 'pr': 'D', }, 'match_hist_and_fut': True,
            'allow_conversion': False, 'allow_resampling': False, 'restrict_members': {'ordered': 1}, 'periods': ['1950', '2100'],
            'exclusions': None, 'other_search_criteria': {'processing_level': 'raw', 'experiment': ['ssp585'], 'source': ['TaiESM1']}}
        #**config['extraction']['simulation']['search_data_catalogs']
    )
    sim_id = list(cat_sim.keys())
    return sim_id

def official_diags_inputfiles_ref(wildcards):
    ref=[]
    step_dict=config['off-diag']['steps']["ref"]
    for dom_name, dom_dict in config['off-diag']['domains'].items():
        ref.append(Path(config['paths']['final'])/f"reference/ref_{step_dict['domain'][dom_name]}_default.zarr")
    return ref

def official_diags_inputfiles_sim(wildcards):
    sim = []
    step_dict = config['off-diag']['steps']["sim"]
    for dom_name, dom_dict in config['off-diag']['domains'].items():
        # iter over step (ref, sim, scen)
        sim.append(Path(config['paths']['exec_workdir'])/f"ESPO-G_workdir/{wildcards.sim_id}_{step_dict['domain'][dom_name]}_regridded.zarr")
    return sim

def official_diags_inputfiles_scen(wildcards):
    scen = []
    for dom_name, dom_dict in config['off-diag']['domains'].items():
        scen.append(Path(config['paths']['final'])/f"FINAL/NAM/day_{wildcards.sim_id}_NAM_1950-2100.zarr")
    return scen

def indname_name_func():
    mod = xs.indicators.load_xclim_module(**config['indicators']['load_xclim_module'])
    indicator = []
    for indname, ind in mod.iter_indicators():
        indicator.append(indname)
    return indicator

def iter_freq():
    region_name = list(config["custom"]["regions"].keys())
    sim_id_name = wildcards_sim_id()
    indname_name = indname_name_func()

    inputfiles = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/tmp/{sim_id}_{region}_{indname}.zarr",sim_id=sim_id_name,region=region_name,indname=indname_name)
    freqs=[]
    for file in inputfiles:
        ds = xr.open_zarr(file)
        freqs.append(ds.attrs['cat:xrfreq'])
    freqs = list(set(freqs))
    return freqs

def experiment_name():
    experiment=[]
    input = [expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_indicators.zarr",sim_id=wildcards_sim_id(),xrfreq=iter_freq()),
            expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_climatology.zarr",sim_id=wildcards_sim_id(),xrfreq=iter_freq()),
            expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_abs_delta.zarr",sim_id=wildcards_sim_id(),xrfreq=iter_freq()),
            expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_per_delta.zarr",sim_id=wildcards_sim_id(),xrfreq=iter_freq())]
    for files in input:
        for f in files:
            ind_df = xr.open_zarr(f)
            # iterate through available xrfreq, exp and variables
            experiment.append(ind_df.attrs['cat:experiment'])
            experiment = list(set(experiment))
    return experiment

def varible_indicator():
    variable = []
    input = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_indicators.zarr",sim_id=wildcards_sim_id(),xrfreq=iter_freq())
    for file in input:
        ind_df = xr.open_zarr(file)
        groupe = zarr.open_group(ind_df, mode='r')
        for name, group in groupe.groups():
            variable.append(name)
    return variable

def varible_climatology():
    variable = []
    input = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_climatology.zarr",sim_id=wildcards_sim_id(),xrfreq=iter_freq())
    for file in input:
        ind_df = xr.open_zarr(file)
        groupe = zarr.open_group(ind_df, mode='r')
        for name, group in groupe.groups():
            variable.append(name)
    return variable

def varible_abs_delta():
    variable = []
    input = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_abs_delta.zarr",sim_id=wildcards_sim_id(),xrfreq=iter_freq())
    for file in input:
        ind_df = xr.open_zarr(file)
        groupe = zarr.open_group(ind_df, mode='r')
        for name, group in groupe.groups():
            variable.append(name)
    return variable

def varible_per_delta():
    variable = []
    input = expand(Path(config['paths']['exec_workdir']) / "ESPO-G_workdir/{sim_id}_NAM_{xrfreq}_per_delta.zarr",sim_id=wildcards_sim_id(),xrfreq=iter_freq())
    for file in input:
        ind_df = xr.open_zarr(file)
        groupe = zarr.open_group(ind_df, mode='r')
        for name, group in groupe.groups():
            variable.append(name)
    return variable