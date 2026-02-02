from copy import deepcopy
from pathlib import Path
import xarray as xr
import xscen as xs
import xsdba as xa
try:
    from workflow.scripts.utils import dask_cluster, tmp_zarr_and_zip
except ImportError:
    from inpact.scripts.utils import save_to_zarrzip as tmp_zarr_and_zip
    from inpact.scripts.utils import dask_cluster
import datetime
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    var = snakemake.wildcards.var
    input_train = snakemake.input.train
    input_rechunk = snakemake.input.rechunk
    input_scen = snakemake.input.scen
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)
    
    # Start Dask cluster
    client=dask_cluster(
        n_workers=snakemake.params.n_workers,
        cpus_per_task=snakemake.params.cpus_per_task,
        mem=snakemake.params.mem,
        local_directory=Path(config['tmppath']) / "dask",
        **config['dask'].get('client', {})
        )

    # Load sim ds
    ds_sim = xr.open_zarr(input_rechunk, decode_timedelta=False)
    ds_tr = xr.open_zarr(input_train, decode_timedelta=False)
    ds_scen = xr.open_zarr(input_scen, decode_timedelta=False)

    # Add 'scen' to adjusting args
    args = deepcopy(config['biasadjust_extremes']['variables'][var]['adjusting_args'])
    args["xsdba_adjust_args"] = args.get("xsdba_adjust_args", {})
    args["xsdba_adjust_args"]["scen"] = ds_scen[var]

    # Adjust
    ds_scen = xs.adjust(
        dsim=ds_sim,
        dtrain=ds_tr,
        **args
        )

    #FIXME: until xscen>=0.13.1, add ba_ref by hand
    if ds_scen.attrs.get('cat:bias_adjust_reference', 'unknown') == 'unknown':
        if ds_tr.attrs.get('cat:bias_adjust_reference') is not None:
            ds_scen.attrs['cat:bias_adjust_reference'] = ds_tr.attrs['cat:bias_adjust_reference']
        elif config.get('bias_adjust_reference') is not None:
            ds_scen.attrs['cat:bias_adjust_reference'] = config['bias_adjust_reference']

    # Save
    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(ds_scen, output, rechunk=config['chunks']['working'], encoding={v: {"dtype": "float32"} for v in ds_scen.data_vars})
    else:
        xs.save_to_zarr(ds_scen, output, rechunk=config['chunks']['working'], encoding={v: {"dtype": "float32"} for v in ds_scen.data_vars})
