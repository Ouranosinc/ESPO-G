from copy import deepcopy
from pathlib import Path
import xscen as xs
import xarray as xr
xr.set_options(keep_attrs=True)
try:
    from workflow.scripts.utils import tmp_zarr_and_zip
except ImportError:
    from inpact.scripts.utils import save_to_zarrzip as tmp_zarr_and_zip
from xscen.xclim_modules import conversions
from pathlib import Path
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    coords = snakemake.input[0]
    input = snakemake.input[1:]
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)
    
    # Get all adjusted data
    ds = xr.open_mfdataset(input, engine='zarr', decode_timedelta=False)

    # Compute tasmin from dtr and tasmax
    if "tasmin" not in ds.data_vars:
        conv_mod = xs.indicators.load_xclim_module(Path(conversions.__file__).with_suffix(""))
        ds = ds.assign(tasmin=conv_mod.tasmin_from_dtr(dtr=ds.dtr, tasmax=ds.tasmax))
    else:
        ds["tasmin"] = ds["tasmin"].clip(max=ds["tasmax"] - 0.01)
    # FIXME: This is a temporary addon to test both methods.
    if "dtr" not in ds.data_vars:
        ds["dtr"] = ds["tasmax"] - ds["tasmin"]
        ds["dtr"].attrs = {"units": "K", "long_name": "diurnal temperature range"}

    args = deepcopy(config['clean_up']['xscen_clean_up'])
    if "maybe_unstack_dict" in args and "coords" not in args["maybe_unstack_dict"]:
        args["maybe_unstack_dict"]["coords"] = str(coords)

    ds = xs.clean_up(ds=ds,**args)
    for dim in ds.dims:
        if "original_shape" in ds[dim].attrs:
            del ds[dim].attrs["original_shape"]

    ds.attrs['cat:_data_format_'] = 'zarr'
    ds.attrs['cat:date'] = 'zarr'

    chunks=xs.utils.translate_time_chunk(
        config['chunks']['final'],
        calendar=ds.time.dt.calendar,
        timesize=ds.time.size,)

    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(ds, output, itervar=True, rechunk=chunks, encoding={v: {"dtype": "float32"} for v in ds.data_vars}, **config['clean_up']['save'])
    else:
        xs.save_to_zarr(ds, output, itervar=True, rechunk=chunks, encoding={v: {"dtype": "float32"} for v in ds.data_vars}, **config['clean_up']['save'])
