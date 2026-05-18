from copy import deepcopy
import xarray as xr
import xscen as xs
import xclim as xc
import xsdba as xa
import numpy as np
import os
from xsdba.base import Grouper, map_blocks, map_groups
from xsdba.nbutils import quantile
import datetime


if __name__ == '__main__':

    # find q99 in reg
    # dreg=[]
    # for i in range(6):
    #     dreg.append(xr.open_zarr(f"/scratch/julavoie/espo-workdir-23avr/CMIP6_CORDEX_CanESM5-1_r1i1p1f2_CCCma_CanRCM5-SN_ssp370_r2_NAM-25+NAM+CaSR+sr-{i}+regchunked.zarr"))
    # ds_reg=xr.concat(dreg, dim='loc')

    # simcal = xc.core.calendar.get_calendar(ds_reg)
    # mincal = xs.utils.minimum_calendar(simcal, 'noleap')
    # ds_reg=ds_reg.convert_calendar(mincal)

    # ds_reg_clim=ds_reg.sel(time=slice('1991','2020')).chunk({'loc':600,'time':-1})
    # g=Grouper('time.dayofyear', window=31)
    
    # groupby_obj_reg =g.group(ds_reg_clim.pr)
    
    # q99_reg = groupby_obj_reg.map(lambda x: quantile(x, [0.99], dim=['time', 'window']))
    # q99_reg=q99_reg.to_dataset(name='pr')
    # q99_reg=q99_reg.rename({'dayofyear':'time'}).squeeze().drop_vars('quantiles')
    # q99_reg=q99_reg.chunk({'loc':600,'time':-1})
    # for v in q99_reg.coords:
    #     if 'chunks' in q99_reg[v].encoding:
    #         del q99_reg[v].encoding['chunks']

    # xs.save_to_zarr(q99_reg, f"/scratch/julavoie/tmp/q99_reg.zarr",)

  
    # q99_reg= xr.open_zarr(f"/scratch/julavoie/tmp/q99_reg.zarr")

    

    # q99= xr.concat([q99_reg]*150, dim='time')
    # q99['time']=ds_reg['time']

    # mask10 = ds_reg.pr >= 10 *q99.pr

    # mask1000 = ds_reg.pr >= 1000 *q99.pr

    # mask10=mask10.chunk({'loc':600,'time':-1})
    # mask1000=mask1000.chunk({'loc':600,'time':-1})

    # print(mask10)



    # xs.save_to_zarr(mask10.to_dataset(), f"/scratch/julavoie/tmp/mask10.zarr",)
    # xs.save_to_zarr(mask1000.to_dataset(), f"/scratch/julavoie/tmp/mask1000.zarr",)

    mask10= xr.open_zarr(f"/scratch/julavoie/tmp/mask10.zarr").pr
    mask1000= xr.open_zarr(f"/scratch/julavoie/tmp/mask1000.zarr").pr


    mask10=mask10.where(mask10.compute(), drop=True)
    mask1000=mask1000.where(mask1000.compute(), drop=True)


    df10 = mask10.to_dataframe().reset_index()
    df10 = df10.dropna(subset=['pr'])



    df10.to_csv(f"/scratch/julavoie/tmp/mask10.csv")
    df1000 = mask1000.to_dataframe().reset_index()
    df1000= df1000.dropna(subset=['pr'])
    df1000.to_csv(f"/scratch/julavoie/tmp/mask1000.csv")