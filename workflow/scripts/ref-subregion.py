from pathlib import Path
from copy import deepcopy
import xarray as xr
import xscen as xs
from workflow.scripts.utils import tmp_zarr_and_zip
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    input = snakemake.input[0]
    output_default = snakemake.output.default
    output_noleap = snakemake.output.noleap
    output_day360 = snakemake.output.day360
    coords = snakemake.output.coords
    subregion = snakemake.wildcards.subregion
    config = deepcopy(snakemake.config)

    ds_ref = xr.open_zarr(input, decode_timedelta=False)

    # Subset the subregion
    ds_ref = xs.spatial.subset(ds_ref, **config['custom']['regions'][subregion])
    
    # The subset puts NaNs in the mask for rotated grids
    if "mask" in ds_ref:
        ds_ref["mask"] = ds_ref["mask"].fillna(0)

    # Stack
    Path(coords).parent.mkdir(parents=True, exist_ok=True)  # 'stack_drop_nans' currently can't create subfolders
    ds_ref = xs.utils.stack_drop_nans(
        ds_ref,
        ds_ref["mask"].astype(bool).load(),
        to_file=str(coords)
    )

    # FIXME: Precomputing the calendar conversions here is probably not necessary anymore.
    # default calendar
    ds_ref.attrs['cat:calendar'] = 'default'
    tmp_zarr_and_zip(ds_ref, output_default, rechunk=config['chunks']['working'], encoding={v: {"dtype": "float32"} for v in ds_ref.data_vars})

    # noleap
    ds_refnl = ds_ref.convert_calendar('noleap')
    ds_refnl.attrs['cat:calendar'] = 'noleap'
    tmp_zarr_and_zip(ds_refnl, output_noleap, rechunk=config['chunks']['working'], encoding={v: {"dtype": "float32"} for v in ds_refnl.data_vars})

    # 360_day
    ds_ref3 = ds_ref.convert_calendar('360_day', align_on="year")
    ds_ref3.attrs['cat:calendar'] = '360_day'
    tmp_zarr_and_zip(ds_ref3, output_day360, rechunk=config['chunks']['working'], encoding={v: {"dtype": "float32"} for v in ds_ref3.data_vars})
    