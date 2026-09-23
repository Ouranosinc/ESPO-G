"""Regrid simulation on reference grid."""

from copy import deepcopy

import xarray as xr
import xscen as xs


if 1 == 0:  # trick vscode
    import snakemake


if __name__ == "__main__":
    # Get Snakemake parameters
    config = deepcopy(snakemake.config)
    inputs = snakemake.input
    output = snakemake.output[0]

    # client=dask_cluster(snakemake.params,config['dask']['client'])

    ds_input = xr.open_zarr(inputs["extract"], decode_timedelta=False)  # .compute()
    ds_input = ds_input.drop_vars("crs", errors="ignore")

    ds_target = xr.open_zarr(inputs["ref"], decode_timedelta=False).compute()

    # Adjust intermediate grids
    if "intermediate_grids" in config["regrid"]["regrid_dataset"]:
        intermediate_grids = deepcopy(
            config["regrid"]["regrid_dataset"]["intermediate_grids"]
        )
        grids = deepcopy(intermediate_grids)
        est_res = xs.spatial._estimate_grid_resolution(ds_input)
        for key, grid_info in grids.items():
            if (
                grid_info["cf_grid_2d"]["d_lon"] > est_res[0]
                or grid_info["cf_grid_2d"]["d_lat"] > est_res[1]
            ):
                # Delete intermediate grids that are too coarse
                intermediate_grids.pop(key)
                print(
                    f"Pop grid {key} with resolution {grid_info['cf_grid_2d']['d_lon']}x{grid_info['cf_grid_2d']['d_lat']} because it is coarser than the estimated input grid resolution {est_res[0]}x{est_res[1]}"
                )

        if len(intermediate_grids) > 0:
            config["regrid"]["regrid_dataset"]["intermediate_grids"] = (
                intermediate_grids
            )
        else:
            config["regrid"]["regrid_dataset"].pop("intermediate_grids")

    ds_regrid = xs.regrid_dataset(
        ds=ds_input, ds_grid=ds_target, **config["regrid"]["regrid_dataset"]
    )

    # save
    xs.save_to_zarr(ds_regrid, output, **config["save_to_zarr"])
