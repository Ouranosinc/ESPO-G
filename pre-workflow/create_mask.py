
import xscen as xs
import xarray as xr
from xscen import CONFIG
import datetime
import numpy as np

xs.load_config("../config/config_general.yml", "../config/config_region.yml", "../config/paths.yml")



if __name__ == '__main__':

    cat = xs.DataCatalog(CONFIG['reccat'])
    pcat = xs.ProjectCatalog(
        CONFIG['espoinput'],
        create=True,
        project={'title': 'ESPO-input', 'description': ' Inputs for ESPO'}
    )

    ds= cat.search(source=[ 'CaSR'], variable=['sftof'], frequency='fx').to_dataset()
    # start with removing the ocean
    mask= xr.where(ds.sftof==1, np.nan, 1)

    # add back a buffer along the coast
    w = xs.spatial.creep_weights(mask.notnull())
    mask = xs.spatial.creep_fill(mask, w)

    # flip in bool and dataset
    mask= xr.where(mask==1, True, False).to_dataset(name='mask')

    # attrs
    mask.attrs=ds.attrs
    mask['mask'].attrs['Description']='The mask was created in 2 steps. First, the grid cells that have sftof=1 are removed. Then, a buffer along the coast is added using the function xscen.spatial.creep_fill.'
    mask['mask'].attrs['long_name']= 'Mask for ESPO'

    mask.attrs['cat:variable']='mask'
    mask.attrs['cat:format']='zarr'
    new_history = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Mask for ESPO computed at Ouranos from sftof."
    history = getattr(ds.attrs, "history", '') +" \n " + new_history
    mask.attrs["history"] = history
    for c in ds.coords:
        mask[c].attrs=ds[c].attrs

    # save
    path=f"{xs.build_path(mask, root=CONFIG['data'])}.zip"
    print(mask)
    print(path)
    xs.save_to_zarr(mask, path.replace('.zip', ''))
    xs.io.zip_directory(path.replace('.zip', ''), path, delete=True)
    #tmp_zarr_and_zip(mask,path )
    pcat.update_from_ds(mask, path)

