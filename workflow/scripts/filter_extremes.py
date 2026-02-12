from copy import deepcopy
import xarray as xr
import xscen as xs
import xclim as xc
import xsdba as xa
import numpy as np
from workflow.scripts.utils import dask_cluster
from xsdba.base import Grouper, map_blocks, map_groups
from xsdba.nbutils import quantile
import datetime
if 1==0: #trick vscode
    import snakemake


if __name__ == '__main__':
    # Get Snakemake parameters
    input_rechunk = snakemake.input.rechunk
    input_adjusted = snakemake.input.adjusted
    output = snakemake.output[0]
    config = deepcopy(snakemake.config)

    client=dask_cluster(snakemake.params, config['dask']['client'])

    # find q99 in reg
    ds_reg= xr.open_zarr(input_rechunk)

    simcal = xc.core.calendar.get_calendar(ds_reg)
    mincal = xs.utils.minimum_calendar(simcal, 'noleap')
    ds_reg=ds_reg.convert_calendar(mincal)

    ds_reg_clim=ds_reg.sel(time=slice('1991','2020')).chunk(config['chunks']['workingloc'])
    g=Grouper('time.dayofyear', window=31)
    
    groupby_obj_reg =g.group(ds_reg_clim.pr)
    
    q99_reg = groupby_obj_reg.map(lambda x: quantile(x, [0.99], dim=['time', 'window']))
    q99_reg=q99_reg.to_dataset(name='pr')

  
    # replace adjusted pr with reg pr when reg pr was above 1000 q99
    ds_adj= xr.open_zarr(input_adjusted)

    q99_reg=q99_reg.rename({'dayofyear':'time'}).squeeze().drop_vars('quantiles')
    q99= xr.concat([q99_reg]*150, dim='time')
    print(q99)
    print(ds_adj)
    q99['time']=ds_adj['time']

    ds_adj['pr']= ds_adj['pr'].where((ds_adj.pr < config['filter_extremes']['factor'] *q99).compute(), other=ds_reg.pr)

    xs.save_to_zarr(ds_adj, output, **config['save_to_zarr'])