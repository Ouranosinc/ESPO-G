# ESPO-G


## Licenses 
|Model |License|
|---|---|
|BCC-CSM2-MR|CC BY 4.0|
|FGOALS-g3|CC BY 4.0|
|CMCC-ESM2| CC BY 4.0|
|CNRM-ESM2-1|CC BY 4.0|
|ACCESS-CM2|CC BY 4.0|
|ACCESS-ESM1-5|CC BY 4.0|
|MPI-ESM1-2-HR| CC BY 4.0|
|INM-CM5-0|CC BY 4.0|
|MIROC6|CC BY 4.0|
|MPI-ESM1-2-LR| CC BY 4.0| 	
|MRI-ESM2-0|CC BY 4.0|
|NorESM2-LM|CC BY 4.0|
|KACE-1-0-G|CC BY 4.0|
|GFDL-ESM4| CC BY 4.0| 

Source: https://wcrp-cmip.github.io/CMIP6_CVs/docs/CMIP6_source_id_licenses.html



# ESPO-G : Ensemble de scénarios polyvalents d'Ouranos - Global / Ouranos' Multipurpose Global Climate Scenarios

## Context
The need to adapt to climate change is present in a growing number of fields, leading to an increase in the demand for 
climate scenarios for often interrelated sectors of activity. In order to meet this growing demand and to ensure the 
availability of climate scenarios responding to numerous vulnerability, impact, and adaptation (VIA) studies, 
[Ouranos](https://www.ouranos.ca) is working to create a set of operational multipurpose climate scenarios called 
"Ensemble de Scénarios Polyvalents d'Ouranos" (ESPO) covering North America at a resolution of 0.1 degree (~9km).
This operational product consists of two related datasets 1) ESPO-R (https://github.com/Ouranosinc/ESPO-R) produced from bias-adjusted regional
climate simulations, and 2) ESPO-G (described here) produced following the same methodology, but from global simulations available via the CMIP program.

## ESPO-G6 v1.0
ESPO-R5 v1.0 is an analysis-ready climate projection ensemble based on simulations from different global climate models (GCMs). 
The full list of simulations that compose the ensemble is shown in the table below. Following Hausfather et al. (2022), the selected model all fall in the Transient Climate Response likely range.
The simulation ensemble covers the period for years 1950-2100 and includes the daily minimum temperature (`tasmin`), the daily maximum temperature (`tasmax`) and the daily mean precipitation flux (`pr`).
The experiments included are SSP2-4.5, SSP3-7.0 and SSP5-8.5.
Simulations are bias-adjusted using the ERA5-Land reference dataset.

**Table 1. Members of ESPO-G6 v1.0.**

|**Institution**|**Model** |**Member** |**License**|
|---|---|---|---|
|CAS |	FGOALS-g3 |	r1i1p1f1 |CC BY 4.0|
|CMCC 	|CMCC-ESM2 |	r1i1p1f1 |CC BY 4.0|
|	CSIRO-ARCCSS |	ACCESS-CM2 |	r1i1p1f1  |CC BY 4.0|
| CSIRO 	|ACCESS-ESM1-5 |	r1i1p1f1 |CC BY 4.0|
| 	DKRZ |	MPI-ESM1-2-HR |	r1i1p1f1 |CC BY 4.0|
| 	INM 	|INM-CM5-0 |	r1i1p1f1 |CC BY 4.0|
| 	MIROC |	MIROC6 |	r1i1p1f1 |CC BY 4.0|
| 	MPI-M |	MPI-ESM1-2-LR |	r1i1p1f1 |CC BY 4.0|
| 	MRI |	MRI-ESM2-0 |	r1i1p1f1 |CC BY 4.0|
| 	NCC |	NorESM2-LM |	r1i1p1f1 |CC BY 4.0|
| 	CNRM-CERFACS |	CNRM-ESM2-1 |	r1i1p1f2 |CC BY 4.0|
| 	NIMS-KMA |	KACE-1-0-G |	r1i1p1f1 |CC BY 4.0|
| 	NOAA-GFDL |	GFDL-ESM4 |	r1i1p1f1 |CC BY 4.0|
| 	BCC |	BCC-CSM2-MR |	r1i1p1f1 |CC BY 4.0|

### Spatial coverage
The dataset has a resolution of 0.1° over a domain corresponding to (almost) the largest common area covered by all
simulations when using this resolution in a Plate Carrée coordinate system: from 147.5°W to 52.7°W and from 19.3°N to 74.2°N.
In order to have the ESPO-R domain fully cover a few islands at the northern boundary of the domain, we had
to extend it slightly further than the common area. As such, the region from 71.2°N to 74.2°N  is fully covered by only
15 members. Data is only available on land, as the reference dataset (ERA5-Land) is only defined there.

The following map shows the domain and the diagnostic regions used when assessing the performance of the bias adjustment.
![domain](../images/regions_domain_map.pdf)

### Temporal coverage
As the bias-adjustment method requires a consistent number of calendar days (no leap days), all members using a standard
calendar were converted to the noleap one by dropping any values for February 29th. `KACE-1-0-G`
is the only model simulated with a 360-day calendar, and was kept as is.

The bias-adjustment was calibrated over the years 1991-2010, following the WMO recommendation for reference periods, and applied to the full 1950-2100 period.

### Reference data
For uniformity, ESPO-G6 v1.0 uses the same reference dataset as ESPO-R5 v1.0. This section describes the analysis that was done to chose the reference dataset.
ESPO-R5 v1.0 uses the [ERA5-Land reanalysis](https://confluence.ecmwf.int/display/CKB/ERA5-Land) (Muñoz Sabater, J., 2019 & 2021)
as its reference (or target) dataset. ERA5-Land is a re-run of the land component of the ERA5 climate reanalysis,
forced by meteorological fields from ERA5 and cover the period from 1950 to the present (with a 2-3 month lag from present day for data quality assurance reasons).
ERA5-Land benefits from numerous improvements, making it more accurate for all types of land applications than the original ERA5; 
Specifically, ERA5-Land runs at an enhanced resolution (~9 km vs ~31 km in ERA5).

Depending on the simulation to adjust, the ERA5-Land data was converted to a "noleap" or to a "360_day" calendar.
In the first case, all instances of February 29th are dropped. In the second case, five (5) or six (6) days per year are
dropped, chosen to be uniformly distributed as detailed in
[xclim's documentation](https://xclim.readthedocs.io/en/stable/api.html?highlight=convert_calendar#xclim.core.calendar.convert_calendar).

ERA5-Land was retained after an evaluation of multiple candidate datasets (Table 1) against observed data for the 
variables of daily maximum and minimum temperatures, and daily total precipitation for the period 1981-2010.  
Observed data for the comparison consisted of Third Generation of Homogenized Daily Temperature for Canada (Vincent et al. 2020), 
as well as Second Generation of Daily Adjusted Precipitation for Canada (AHCCD; Mékis and Vincent. 2011). To be included
in the assessment, adjusted station data had to have 25 years of valid data for the period 1981-2010 and a valid year requiring 
each month to have no more than 10% missing data.

The evaluation criteria included: 
1) a comparison of the mean annual cycle (figure 1), 
2) an evaluation of the inter-annual seasonal time series (figures 2a-c), and 
3) a seasonal evaluation of the quantile bias (5, 25 , 50, 75, 95) of the daily values between station data and the various candidates (figures 3a-b). 

The summary results of quantitative comparisons (figures 1 to 3) indicate that there is no clear winner for the choice of 
reference dataset, with results varying by season or criteria. As such, ERA5-Land was chosen because it generally shows
good results while presenting the advantages of an increased spatial and temporal resolution as well as a temporal
coverage up to the present (Table 2).

**Table 2. Summary of reference dataset candidates for ESPO.**

| Dataset             | Start year | End year    | Spatial coverage       | Spatial resolution | Temporal resolution | Reference                               |
|---------------------|------------|-------------|------------------------|--------------------|---------------------|-----------------------------------------| 
| ERA5                | 1979       | Present     | global                 | ~32 Km             | 1 h                 | Hersbach et al. 2018                    |
| **ERA5-Land**       | **1979**   | **Present** | **global (land only)** | **~9 Km**          | **1 h**             | **Muñoz-Sabater, J. et al. 2019, 2021** |
| NCEP Reanalysis 2   | 1979       | Present     | global                 | 2.5 x 2.5 degrees  | 6 h                 | Kanamitsu et al. 2002                   |
| NCEP CFSR           | 1979       | 2009        | global                 | ~40 Km             | 1 h                 | Saha et al. 2010                        |
| MERRA2              | 1980       | Present     | global                 | ~50 Km             | 3 h                 | Gelaro, et al. 2017                     |
| AgCFSR              | 1979       | 2010        | global (land only)     | ~30 Km             | 1 h                 | Ruane et al. 2015                       |
| AgMERRA             | 1979       | 2010        | global (land only)     | ~30 Km             | 1 h                 | Ruane et al. 2015                       |
| WFDEI-GEM-CaPa      | 1979       | 2016        | global (land only)     | ~10 Km             | 1 h                 | Asong et al. 2020                       |
| NRCAN Gridded v2017 | 1950       | 2017        | Canada (land only)     | ~10 Km             | 1 day               | McKenney et al. 2011                    |


![img.png](images/img.png)

**Figure 1.** Summary of assessment of mean annual cycle (1981-2010) between candidate datasets and adjusted station data for daily maximum temperature (left column), daily minimum temperature (middle column) and total precipitation (right column). The figures represent the distribution of mean square (top) and correlation (bottom) error values between stations and gridded data.

![img_1.png](images/img_1.png)
a)
![img_2.png](images/img_2.png)
b)
![img_3.png](images/img_3.png)
c)

**Figure 2.** Summary of evaluation of inter-annual seasonal time series (1981-2010) between candidate datasets and AHCCD stations for daily maximum temperature (a), daily minimum temperature (b) and daily total precipitation (c) variables ). The figures represent the distribution of mean square (top) and correlation (bottom) error values between stations and gridded data.

![img_4.png](images/img_4.png)
a)
![img.png](images/img_5.png)
b)
![img.png](images/img_6.png)
c)

**Figure 3.** Summary of bias by percentile (1981-2010) between candidate datasets for daily values of maximum temperatures (a), minimum temperatures (b) and total precipitation (c). The comparison was made for the seasons of winter (DJF: 1st column), spring (MAM: 2nd column), summer (JJA: 3rd column) and autumn (SON: 4th column). The results for the compared percentiles (5, 25, 50, 75, and 95) are organized by row in ascending order, starting from the top.


### Methodology
The workflow to prepare ESPO-G6 v1.0 was built with [xscen](https://github.com/Ouranosinc/xscen).
The temperature and precipitation data from the simulations in table 2 were first extracted over North America.
Then, all the extracted simulation data is interpolated bilinearly in cascade to the ERA5-Land grid.

The ESPO-G6 v.1.0 bias adjustment procedure then uses [xclim's bias adjustment algorithms](https://xclim.readthedocs.io/en/stable/sdba.html)
to adjust simulation bias following a quantile mapping procedure. In particular, the algorithm used is inspired by the
"Detrended Quantile Mapping" (DQM) method described by Cannon (2015). The procedure is bipartite;
First, the adjustment factors are calculated based on reference data and simulations over a common period (training stage),
and second, the entire simulation is corrected with these factors (adjustment step). The reference period chosen here were years 1991-2020.
Adjustments are univariate, where corrections are applied separately for each of the 3 variables. Data is adjusted for
each day of the year, using a rolling window of 31 days. Although computational more expensive, the rolling window method
allows for better adjustment of the annual cycle. Note that this method does not work well with leap years as there is four
(4) times fewer data values for day 366. To remedy this problem, all simulations as well as the reference product are
converted to this "noleap" calendar. A more detailed explanation of the adjustment process is given in [the documentation](Documentation/adjustment.pdf).

## Data processing tools
Production and regular updates of ESPO-R/G operational datasets represents a challenge in terms of computational resources. 
Ouranos has invested a great deal of effort in the development of powerful tools for this type of data processing via its 
[xclim software package](https://xclim.readthedocs.io/en/stable/) (Logan et al., 2021). Built upon the packages
[xarray](https://xarray.dev/) and [dask](https://www.dask.org/), xclim benefits from simple-to-use parallelization and
distributed computing tools and can be easily deployed in High Performance Computing (HPC) environments.

This repository contains the code used to generate and analyze the ESPO-G datasets. In addition to xclim and other
freely available python libraries, it also uses [xscen](https://github.com/Ouranosinc/xscen), a climate change
scenario-building analysis framework, also being developed at Ouranos. This tool relies on data catalogs as handled by
[intake-esm](https://intake-esm.readthedocs.io/en/latest/index.html) as well as on YAML configuration files with a
simple but specific structure. The catalog files and all paths needed by the configuration are missing from this
repository, since they are specific to the data architecture of the computer running the code. To reproduce ESPO-G, one will need:

- `simulation.json` and `simulation.csv` :An intake-esm catalog, compatible with xscen, listing the daily simulation datasets to use as inputs.
- `reconstruction.json` and `reconstruction.csv` :An intake-esm catalog, compatible with xscen, listing the daily reference datasets to use as inputs.
- `paths_ESPO-G.yml`: A yaml file with the paths needed by the workflows. `template_paths.yml` shows an example of such a file, one only needs to replace the placeholders.

To run the workflow, uncomment the tasks wanted at the top of the config. Then, run

``python workflow_ESPO-G.py``

### Performance
Bias-adjustment of climate simulations is a quest with many traps. In order to assess the improvements and regressions
that the process brought to the simulations, we emulated the "VALUE" validation framework (Maraun et al., 2015).
While that project aimed to "to validate and compare downscaling methods", we based our approach on its ideas of statistical
"properties" and "measures" to measure bias between the simulations, the scenarios, and the reference.

A detailed analysis is given in [the documentation](Documentation/performance.pdf).
Our general conclusions concerning the quality of ESPO-R6v1.0 are:

 - The marginal properties of the simulations (mean, quantiles) are very well-adjusted, by design of the Quantile Mapping algorithm.
 - The climate change signal is also conserved from the simulations by design of the algorithm.
 - A side effect of adjusting the distributions explicitly is the improvement of the inter-variable correlation, even though the bias correction algorithm does not aim to adjust these aspects.
 - Because tasmin is not directly adjusted, but rather computed from the adjusted tasmax and dtr, it seems that our diagnostics show weaker improvements, compared to tasmax.

A subset of the properties and measures discussed in the performance analysis is made available in this repository, in the `data/` folder.

## Data availability and download
The ESPO-R6v1.0 data is currently available under the [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) license. [[ TODO: verify this!!]]

At the time of publication, the data is stored on [Ouranos](https://www.ouranos.ca/)' THREDDS server, a part of the [PAVICS](https://pavics.ouranos.ca/) project:

LINK

When new versions of ESPO-G will be released, previous versions may be pulled from the server. [Please contact us](mailto:scenarios@ouranos.ca) if you wish to obtain these.

## Acknowledgements
We acknowledge the World Climate Research Programme, which, through its Working Group on Coupled Modelling, coordinated and promoted CMIP6. We thank the climate modeling groups for producing and making available their model output, the Earth System Grid Federation (ESGF) for archiving the data and providing access, and the multiple funding agencies who support CMIP6 and ESGF.


The ESPO-G6 data was generated using ERA5-Land hourly data from 1950 to present (https://doi.org/10.24381/cds.e2161bac)
made available through the Copernicus Climate Change Climate Data Store (https://cds.climate.copernicus.eu).

## References
Asong, Z. E., Elshamy, M. E., Princz, D., Wheater, H. S., Pomeroy, J. W., Pietroniro, A., and Cannon, A. (2020): High-resolution meteorological forcing data for hydrological modelling and climate change impact analysis in the Mackenzie River Basin, Earth Syst. Sci. Data, 12, 629–645, https://doi.org/10.5194/essd-12-629-2020.

Cannon, A. J., Sobie, S. R., & Murdock, T. Q. (2015). Bias correction of GCM precipitation by quantile mapping: How well do methods preserve changes in quantiles and extremes? Journal of Climate, 28(17), 6938–6959. https://doi.org/10.1175/JCLI-D-14-00754.1

DeLuca, C., Theurich, G., & Balaji, V. (2012). The Earth System Modeling Framework. In S. Valcke, R. Redler, & R. Budich (Eds.), Earth System Modelling—Volume 3: Coupling Software and Strategies (pp. 43–54). Springer. https://doi.org/10.1007/978-3-642-23360-9_6

Gelaro, R., McCarty, W., Suarez, M. J., Todling, R., Molod, A., Takacs, L., et al. (2017). The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2). J. Clim., doi: 10.1175/JCLI-D-16-0758.1

Hausfather, Z., Marvel, K., Schmidt, G. A., Nielsen-Gammon, J. W., Zelinka, M. (2022). Climate simulations: recognize the ‘hot model’ problem. Nature 2022 605:7908, 605(7908), 26–29. https://doi.org/10.1038/d41586-022-01192-2

Hersbach H., Bell B., Berrisford P., Biavati G., Horányi A., Muñoz Sabater J., Nicolas J., Peubey C., Radu R., Rozum I., Schepers D., Simmons A., Soci C., Dee D., Thépaut J-N. (2018). ERA5 hourly data on single levels from 1979 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). (Accessed on 15-12-2021), 10.24381/cds.adbb2d47.

Kanamitsu, M., et al , (2002): NCEP-DOE AMIP-II Reanalysis (R-2), Bull. Amer. Meteor. Soc., 83, 1631-1643.

Logan, T., Bourgault, P., Smith, T. J., Huard, D., Biner, S., Labonté, M.-P., Rondeau-Genesse, G., Fyke, J., Aoun, A., Roy, P., Ehbrecht, C., Caron, D., Stephens, A., Whelan, C., Low, J.-F., Keel, T., Lavoie, J., Tanguy, M., Barnes, C., … Quinn, J. (2022). Ouranosinc/xclim (0.35.0) [Python]. Zenodo. https://doi.org/10.5281/zenodo.6407112

Maraun, D., Widmann, M., Gutiérrez,  J.M., Kotlarski, S., Chandler, R. E., Hertig, E., Wibig, J., Huth, R., Wilcke, R. A. I. (2015). VALUE: A Framework to Validate Downscaling Approaches for Climate Change Studies. Earth’s Future 3, 1, 1‑14. https://doi.org/10.1002/2014EF000259.

McKenney, D.W., M.F. Hutchinson, P. Papadol, K. Lawrence, J. Pedlar, K. Campbell, E. Milewska, R.F. Hopkinson, D. Price, and T. Owen, 2011. Customized Spatial Climate Models for North America. Bull. Amer. Meteor. Soc., 92, 1611-1622, https://doi.org/10.1175/2011BAMS3132.1

Mearns, L.O., et al., 2017: The NA-CORDEX dataset, version 1.0. NCAR Climate Data Gateway, Boulder CO,https://doi.org/10.5065/D6SJ1JCH

Mekis, É and L.A. Vincent, 2011: An overview of the second generation adjusted daily precipitation dataset for trend analysis in Canada. Atmosphere-Ocean 49(2), 163-177 doi:10.1080/07055900.2011.583910

Mittermeier, M., Bresson, E., Paquin, D., Ludwig, R., 2021. A deep learning approach for the identification of long-duration mixed precipitation in Montréal (Canada). Atmosphere-Ocean. https://doi.org/10.1080/07055900.2021.1992341

Muñoz Sabater, J., (2019): ERA5-Land hourly data from 1981 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). (Accessed on 15-12-2021), 10.24381/cds.e2161bac

Muñoz Sabater, J., (2021): ERA5-Land hourly data from 1950 to 1980. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). (Accessed on 15-12-2021), 10.24381/cds.e2161bac

Ruane, A.C., R. Goldberg, and J. Chryssanthacopoulos, 2015: AgMIP climate forcing datasets for agricultural modeling: Merged products for gap-filling and historical climate series estimation, Agr. Forest Meteorol., 200, 233-248, doi:10.1016/j.agrformet.2014.09.016

Saha, S., et al. 2010. NCEP Climate Forecast System Reanalysis (CFSR) Selected Hourly Time-Series Products, January 1979 to December 2010. Research Data Archive at the National Center for Atmospheric Research, Computational and Information Systems Laboratory. https://doi.org/10.5065/D6513W89

Vincent, L.A., M.M. Hartwell and X.L. Wang, 2020: A Third Generation of Homogenized Temperature for Trend Analysis and Monitoring Changes in Canada’s Climate. Atmosphere-Ocean. https://doi.org/10.1080/07055900.2020.1765728

Zhuang, J., Dussin, R., Huard, D., Bourgault, P., Banihirwe, A., Raynaud, S., Malevich, B., Schupfner, M., Hamman, J., Levang, S., Jüling, A., Almansi, M., Fernandes, F., Rondeau-Genesse, G., Rasp, S., & Bell, R. (2021). pangeo-data/xESMF (0.6.2) [Python]. Zenodo. https://doi.org/10.5281/zenodo.5721118