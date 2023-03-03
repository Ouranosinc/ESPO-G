import xarray as xr
import logging
from pathlib import Path
import shutil
from matplotlib import pyplot as plt
import os


from xscen.io import save_to_zarr
from xscen.scripting import measure_time, send_mail
from xscen.config import CONFIG, load_config

#load_config('paths_ESPO-G.yml', 'config_ESPO-G.yml', verbose=(__name__ == '__main__'), reset=True)


logger = logging.getLogger('xscen')



def save_move_update(ds,pcat, init_path, final_path,info_dict=None,
                     encoding=None, mode='o', itervar=False, rechunk=None):
    encoding = encoding or {var: {'dtype': 'float32'} for var in ds.data_vars}
    save_to_zarr(ds, init_path, encoding=encoding, mode=mode,itervar=itervar, rechunk=rechunk)
    shutil.move(init_path,final_path)
    pcat.update_from_ds(ds=ds, path=str(final_path),info_dict=info_dict)



def email_nan_count(path, region_name):
    ds_ref_props_nan_count = xr.open_zarr(path, decode_timedelta=False).load()
    fig, ax = plt.subplots(figsize=(10, 10))
    cmap = plt.cm.winter.copy()
    cmap.set_under('white')
    ds_ref_props_nan_count.nan_count.plot(ax=ax, vmin=1, vmax=1000, cmap=cmap)
    ax.set_title(
        f'Reference {region_name} - NaN count \nmax {ds_ref_props_nan_count.nan_count.max().item()}')
    plt.close('all')
    send_mail(
        subject=f'Reference for region {region_name} - Success',
        msg=f"Action 'makeref' succeeded for region {region_name}.",
        attachments=[fig]
    )



def move_then_delete(dirs_to_delete, moving_files, pcat):
    """
    First, move the moving_files. If they are zarr, update catalog
    with new path.
    Then, delete everything in dir_to_delete
    :param dirs_to_delete: list of directory where all content will be deleted
    :param moving_files: list of lists of path of files to move with format: [[source 1, destination1], [source 2, destination2],...]
    :param pcat: project catalog to update
    """

    for files in moving_files:
        source, dest = files[0], files[1]
        if Path(source).exists():
            shutil.move(source, dest)
            if dest[-5:] =='.zarr':
                ds = xr.open_zarr(dest)
                pcat.update_from_ds(ds=ds, path=dest)

    # erase workdir content if this is the last step
    for dir_to_delete in dirs_to_delete:
        if dir_to_delete.exists() and dir_to_delete.is_dir():
            shutil.rmtree(dir_to_delete)
            os.mkdir(dir_to_delete)