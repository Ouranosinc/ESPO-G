# app is here: https://share.streamlit.io/ouranosinc/info-crue-cmip6/main/dashboard.py
import streamlit as st
import holoviews as hv
from pathlib import Path
import pandas as pd
import numpy as np
import xarray as xr
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import glob
import hvplot.xarray
from matplotlib import colors


useCat=True



st.set_page_config(layout="wide")
st.title('Diagnostiques de ESPO-G6')

tab1, tab2 = st.tabs(["properties and measures", "correlogram"])



with tab1:
    if useCat:
        from xscen.config import CONFIG, load_config
        from xscen.catalog import ProjectCatalog
        load_config('paths_ESPO-G.yml', 'config_ESPO-G.yml', verbose=(__name__ == '__main__'), reset=True)
        pcat = ProjectCatalog(CONFIG['paths']['project_catalog'])

        col1, col2, col3 = st.columns([3, 1, 1])

        # choose id
        option_id = st.selectbox('id',sorted(pcat.search(type=['simulations','simulation']).df.id.unique()))
        # choose region
        option_region = st.selectbox('region', pcat.search(type=['simulations','simulation']).df.domain.unique())

        #load all properties from ref, sim, scen
        ref = pcat.search( processing_level=['diag-ref-prop*', 'diag_ref_prop'], domain=option_region).to_dask()
        sim = pcat.search(id= option_id, processing_level='diag-sim-prop*', domain=option_region).to_dask()
        scen = pcat.search(id= option_id, processing_level='diag-scen-prop*', domain=option_region).to_dask()
        #get meas
        meas_sim = pcat.search(id=option_id, processing_level='diag-sim-meas*', domain=option_region).to_dask()
        meas_scen = pcat.search(id=option_id, processing_level='diag-scen-meas*', domain=option_region).to_dask()

        # load hmap
        if option_region != 'NAM':
            hm = pcat.search(domain=option_region,id=scen.attrs['cat:id'],processing_level='diag-heatmap*').to_dask()

            imp = pcat.search(domain=option_region,id=scen.attrs['cat:id'],processing_level='diag-improved*').to_dask()



    # choose properties
    option_var = st.selectbox('Properties',scen.data_vars)
    prop_sim = sim[option_var]
    prop_ref = ref[option_var]
    prop_scen = scen[option_var]
    meas_scen_prop = meas_scen[option_var]
    meas_sim_prop = meas_sim[option_var]

    #colormap
    maxi_prop = max(prop_ref.max().values, prop_scen.max().values, prop_sim.max().values)
    mini_prop = min(prop_ref.min().values, prop_scen.min().values, prop_sim.min().values)
    maxi_meas = max(abs(meas_scen_prop).max().values, abs(meas_sim_prop).max().values)
    cmap='viridis_r' if 'standard_name' in prop_sim and   prop_sim.attrs['standard_name']== 'precipitation_flux' else 'plasma'
    cmap_meas ='BrBG' if 'standard_name' in prop_sim and prop_sim.attrs['standard_name']== 'precipitation_flux' else 'coolwarm'

    long_name=prop_sim.attrs['long_name']


    #
    col1, col2, col3 = st.columns([6,3,4])
    w, h = 300, 300
    wb, hb = 400, 300
    col1.write(hv.render(prop_ref.hvplot(title=f'REF\n{long_name}',width=600, height=616, cmap=cmap, clim=(mini_prop,maxi_prop))))
    col2.write(hv.render(prop_sim.hvplot(width=w, height=h, title=f'SIM', cmap=cmap, clim=(mini_prop,maxi_prop)).opts(colorbar=False)))
    col3.write(hv.render(meas_sim_prop.hvplot(width=wb, height=hb, title=f'SIM meas', cmap=cmap_meas, clim=(-maxi_meas,maxi_meas))))
    col2.write(hv.render(prop_scen.hvplot(width=w, height=h, title=f'SCEN', cmap=cmap, clim=(mini_prop,maxi_prop)).opts(colorbar=False)))
    col3.write(hv.render(meas_scen_prop.hvplot(width=wb, height=hb, title=f'SCEN meas', cmap=cmap_meas, clim=(-maxi_meas,maxi_meas))))



    if option_region != 'NAM':
        #plot the heat map
        fig_hmap, ax = plt.subplots(figsize=(7,3))
        cmap=plt.cm.RdYlGn_r
        norm = colors.BoundaryNorm(np.linspace(0,1,4), cmap.N)
        im = ax.imshow(hm.heatmap.values, cmap=cmap, norm=norm)
        ax.set_xticks(ticks = np.arange(len(hm.properties.values)), labels=hm.properties.values, rotation=45,ha='right')
        ax.set_yticks(ticks = np.arange(len(hm.datasets.values)), labels=[x.split('.')[2].split('-')[1] for x in hm.datasets.values])
        divider = make_axes_locatable(ax)
        cax = divider.new_vertical(size='15%', pad=0.4)
        fig_hmap.add_axes(cax)
        cbar = fig_hmap.colorbar(im, cax=cax, ticks=[0, 1], orientation='horizontal')
        cbar.ax.set_xticklabels(['best', 'worst'])
        plt.title('Normalised mean measure of properties')
        fig_hmap.tight_layout()


        #plot improved

        percent_better= imp.improved_grid_points.values
        percent_better=np.reshape(np.array(percent_better), (1, len(percent_better)))
        fig_per, ax = plt.subplots(figsize=(7, 3))
        cmap=plt.cm.RdYlGn
        norm = colors.BoundaryNorm(np.linspace(0,1,100), cmap.N)
        im = ax.imshow(percent_better, cmap=cmap, norm=norm)
        ax.set_xticks(ticks=np.arange(len(imp.properties.values)), labels= imp.properties.values, rotation=45,ha='right')
        ax.set_yticks(ticks=np.arange(1), labels=[''])

        divider = make_axes_locatable(ax)
        cax = divider.new_vertical(size='15%', pad=0.4)
        fig_per.add_axes(cax)
        cbar = fig_per.colorbar(im, cax=cax, ticks=np.arange(0,1.1,0.1), orientation='horizontal')
        plt.title('Fraction of grid cells of scen that improved or stayed the same compared to sim')
        fig_per.tight_layout()


        col1, col2 = st.columns([1,1])

        col1.write(fig_hmap)
        col2.write(fig_per)

with tab2:
    if useCat:
        from xscen.config import CONFIG, load_config
        from xscen.catalog import ProjectCatalog
        load_config('paths_ESPO-G.yml', 'config_ESPO-G.yml', verbose=(__name__ == '__main__'), reset=True)
        pcat = ProjectCatalog(CONFIG['paths']['project_catalog'])

        # choose id
        option_id_corr = st.selectbox('id ',sorted(pcat.search(type='simulation', processing_level=f'correlogram*').df.id.unique()))
        data ={}
        domains=['Haudenosaunee', 'Ute', 'Dene']
        steps=['sim','scen']
        for dom in domains :
            data[dom]={}
            data[dom]['ref'] = pcat.search(
                processing_level=f'correlogram-ref',
                domain=dom).to_dask(xarray_open_kwargs={'decode_timedelta': False})
            for step in steps:
                data[dom][step] = pcat.search(
                    id= option_id_corr,
                    domain=dom,
                    processing_level=f'correlogram-{step}').to_dask(
                    xarray_open_kwargs={'decode_timedelta':False})

    for var in ['pr', 'tasmax', 'tasmin']:
        cols = st.columns([2,2,2])

        for i,dom in enumerate(domains):
            ds = xr.Dataset()
            for step in ['ref'] + steps:
                #st.write((data[dom][step]))
                ds[step] = data[dom][step][f'correlogram_{var}']
            cols[i].write(hv.render(ds.hvplot(title=f"{var} - {dom}", width=450, height=250)))

