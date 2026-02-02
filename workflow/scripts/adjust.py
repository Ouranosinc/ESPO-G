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

    # load sim ds
    ds_sim = xr.open_zarr(input_rechunk, decode_timedelta=False)
    ds_tr = xr.open_zarr(input_train, decode_timedelta=False)

    if 'hursmin' in ds_sim:
        # trick for biasadjustement of hursmin (sim) on hursTasmax (ref)
        ds_sim = ds_sim.rename({'hursmin': 'hursTasmax'})
        #needed until we can use numpy>2, useful for clip in additive transform
        #ds_sim['hursTasmax'] = ds_sim['hursTasmax'].astype(float)
        #ds_sim['hurs'] = ds_sim['hurs'].astype(float)

    #clip before
    #ds_sim['hurs'] = ds_sim['hurs'].clip(0,100)
    #ds_sim['hursTasmax'] = ds_sim['hursTasmax'].clip(0,100)

    if "dtr" in ds_sim:
        # There are some negative dtr in the data (GFDL-ESM4). This puts is back to a very small positive.
        ds_sim['dtr'] = xa.processing.jitter_under_thresh(ds_sim.dtr, "1e-4 K")

    # adjust
    ds_scen = xs.adjust(
        dsim=ds_sim,
        dtrain=ds_tr,
        **config['biasadjust']['variables'][var]['adjusting_args']
        )

    #FIXME: until xscen>=0.13.1, add ba_ref by hand
    if ds_scen.attrs.get('cat:bias_adjust_reference', 'unknown') == 'unknown':
        if ds_tr.attrs.get('cat:bias_adjust_reference') is not None:
            ds_scen.attrs['cat:bias_adjust_reference'] = ds_tr.attrs['cat:bias_adjust_reference']
        elif config.get('bias_adjust_reference') is not None:
            ds_scen.attrs['cat:bias_adjust_reference'] = config['bias_adjust_reference']

    #FIXME: until xscen>=0.13.1,   final clip here instead of with xscen.clean_up
    new_history = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Clipped to [0,100]"
    if 'hurs' in ds_scen:
        ds_scen['hurs'] = ds_scen['hurs'].clip(0,100)
        ds_scen['hurs'].attrs['history'] = ds_scen['hurs'].attrs.get('history', '') + new_history
    if 'hursTasmax' in ds_scen:
        ds_scen['hursTasmax'] = ds_scen['hursTasmax'].clip(0,100)
        ds_scen['hursTasmax'].attrs['history'] = ds_scen['hursTasmax'].attrs.get('history', '') + new_history

    # Save
    if Path(output).suffix == '.zip':
        tmp_zarr_and_zip(ds_scen, output, rechunk=config['chunks']['working'], encoding={v: {"dtype": "float32"} for v in ds_scen.data_vars})
    else:
        xs.save_to_zarr(ds_scen, output, rechunk=config['chunks']['working'], encoding={v: {"dtype": "float32"} for v in ds_scen.data_vars})
