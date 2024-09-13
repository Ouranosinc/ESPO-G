import xscen as xs
import copy

def wildcards_sim_id():
    args= copy.deepcopy(config['extraction']['simulation']['search_data_catalogs'])
    cat_sim = xs.search_data_catalogs( **args )
    sim_id = list(cat_sim.keys())
    return sim_id

def official_diags_inputfiles_ref(wildcards):
    step_dict=config['off-diag']['steps']["ref"]
    ref=finaldir/f"reference/{ref_source[0]}+{step_dict['domain'][wildcards.diag_domain]}+default.zarr"
    return ref

def official_diags_inputfiles_sim(wildcards):
    step_dict = config['off-diag']['steps']["sim"]
    sim= finaldir/f"regridded/day+{wildcards.sim_id}+{step_dict['domain'][wildcards.diag_domain]}+regchunked.zarr.zip"
    return sim


