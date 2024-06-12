import xscen as xs

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

def wildcards_sim_id():
    cat_sim = xs.search_data_catalogs(
        **config['extraction']['simulation']['search_data_catalogs'])
    sim_id = list(cat_sim.keys())
    return sim_id
