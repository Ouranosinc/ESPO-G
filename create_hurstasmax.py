import xscen as xs
import xarray as xr
from xscen import CONFIG
import xclim as xc
import datetime
from dask.distributed import Client
from workflow.scripts.utils import tmp_zarr_and_zip
import os
import sys

xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")


if __name__ == '__main__':
    client = Client(
        n_workers=2, threads_per_worker=1, memory_limit="250GB",
        local_directory=os.environ['SLURM_TMPDIR'],dashboard_address= 6785
    )
    
    cat = xs.DataCatalog(CONFIG['reccat'])
    pcat = xs.ProjectCatalog(
        CONFIG['espoinput'],
        create=True,
        project={'title': 'ESPO-input', 'description': ' Inputs for ESPO'}
    )

    ds_dict= cat.search(source=['ERA5-Land', 'CaSR'], variable=['tas','tdps', 'hurs'], frequency='1hr').to_dataset_dict()
    for rid, ds in ds_dict.items():
        if not pcat.exists_in_cat(id=rid.split('.')[0], variable='hursTasmax'):
            print(rid)
            ds=ds.sel(time=slice(None,'2021'))

            # trick to avoid nan
            ds = xs.utils.stack_drop_nans(ds,ds['tas'].isel(time=0, drop=True).notnull().compute(),)

            # get hurs 
            if 'hurs' not in ds.data_vars:
                print("Computing hurs from tas and tdps")
                ds['hurs']=xc.atmos.relative_humidity_from_dewpoint(tas=ds.tas,tdps=ds.tdps )

            # cut the computation in 150 parts
            n = int(ds.sizes['loc']/150)
            for i in range(int(sys.argv[1]),int(sys.argv[2])):#151
            #for i in range(151):
                if not os.path.exists(f"{CONFIG['tmppath']}{rid}{i}.zarr"):
                    print(f"Processing part {i}")
                    dscur = ds.isel(loc=slice(i*n, (i+1)*n))


                    #when tas max
                    max_tas_times=dscur.tas.resample(time='1D').apply(lambda x: x.idxmax('time'))
                    dsTasMax = dscur.sel(time=max_tas_times)
                    dsTasMax["time"] = dsTasMax.time.dt.floor('D')
                    dsTasMax["time"]=dsTasMax["time"].isel(loc=0).squeeze()
                    outcur=dsTasMax[['hurs']]
                    outcur=outcur.chunk({'time': 1460,'loc': 50,})
                    xs.save_to_zarr(outcur,f"{CONFIG['tmppath']}{rid}{i}.zarr" )

            # # merge the 5 parts
            # files= [xr.open_zarr(f"{CONFIG['tmppath']}{rid}{i}.zarr") for i in range(151)]
            # out = xr.concat(files, dim='loc')
            
            # out=xs.utils.unstack_fill_nan(out)
            # out=out.rename({'hurs':'hursTasmax'})

            # #gloabl attrs
            # out.attrs=ds.attrs
            # out.attrs['cat:variable']='hursTasmax'
            # out.attrs['cat:xrfreq']='D'
            # out.attrs['cat:frequency']='day'
            # out.attrs['cat:format']='zarr'
            # del out.attrs['history']
            # del out.attrs['frequency']

            # # coords attrs
            # del out.lat.attrs['original_shape']
            # del out.lon.attrs['original_shape']
            # out.time.attrs['long_name'] = 'time'

            # # var attrs
            # out.hursTasmax.attrs['cell_methods'] = 'time: point'
            # out.hursTasmax.attrs['description'] = 'Relative humidity at time of maximum temperature for each day'
            # out.hursTasmax.attrs['long_name'] = "Relative humidity at time of maximum temperature"
            # new_history = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] HursTasmax computed from hourly hurs and tas."
            # history = out.hursTasmax.attrs["history"] +" \n " + new_history
            # out.hursTasmax.attrs["history"] = history
            
            # if 'ERA5-Land' in rid:
            #     out=out.chunk({'time': 1460,
            #                 'lat': 50,
            #                 'lon': 50})
            # else:
            #     out=out.chunk({'time': 1460,
            #                 'rlat': 100,
            #                 'rlon': 100})

            # # save
            # path=f"{xs.build_path(out, root=CONFIG['data'])}.zip"
            # tmp_zarr_and_zip(out,path )


            # pcat.update_from_ds(out, path)