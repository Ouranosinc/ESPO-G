import xscen as xs
import xarray as xr
from pathlib import Path


# exec_wdir = Path(config['paths']['exec_workdir'])
# regriddir = Path(config['paths']['regriddir'])
# refdir = Path(config['paths']['refdir'])
#
# ref_period = slice(*map(str,config['custom']['ref_period']))
# sim_period = slice(*map(str,config['custom']['sim_period']))
# ref_source = config['extraction']['ref_source']

# pcat = xs.ProjectCatalog(config['paths']['project_catalog'], create=True)
# def inter_region():
#     file_ref = []
#     calandar = ["_default.zarr", "_noleap.zarr", "_360_day.zarr"]
#     for region_name in config['custom']['regions'].keys():
#         for cal in calandar:
#             file_ref.append(Path(config['paths']['refdir'])/f"ref_{region_name}{cal}")
#     return file_ref

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