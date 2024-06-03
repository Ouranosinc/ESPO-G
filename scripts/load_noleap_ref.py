import snakemake
import xscen as xs
from xscen import CONFIG
from utils import save_and_update, save_move_update
from pathlib import Path
from xclim.core.calendar import convert_calendar

exec_wdir = Path(CONFIG['paths']['exec_workdir'])
regriddir = Path(CONFIG['paths']['regriddir'])
refdir = Path(CONFIG['paths']['refdir'])

ref_source = CONFIG['extraction']['ref_source']

pcat = xs.ProjectCatalog(CONFIG['paths']['project_catalog'], create=True)

for region_name, region_dict in CONFIG['custom']['regions'].items():
    if (
            "makeref" in CONFIG["tasks"]
            and not pcat.exists_in_cat(domain=region_name, processing_level='nancount', source=ref_source)
    ):
        if not pcat.exists_in_cat(domain=region_name, calendar='noleap', source=ref_source):

                ds_ref = pcat.search(source=ref_source, calendar='default', domain=region_name).to_dask()

                # convert calendars
                ds_refnl = convert_calendar(ds_ref, "noleap")
                save_move_update(ds=ds_refnl,
                                 pcat=pcat,
                                 init_path=f"{exec_wdir}/ref_{region_name}_noleap.zarr",
                                 final_path=snakemake.output[0],
                                 info_dict={'calendar': 'noleap'})
