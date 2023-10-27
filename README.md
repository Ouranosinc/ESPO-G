# ESPO-G6-R2 : Ensemble de Simulations Post-traitées d’Ouranos - Modèles Globaux CMIP6  - RDRS v2.1 / Ouranos Ensemble of Bias-adjusted Simulations - Global models CMIP6 - RDRS v2.1


ESPO-G6:[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7764928.svg)](https://doi.org/10.5281/zenodo.7764928)

ESPO-G6-R2 v1.0.0: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7877330.svg)](https://doi.org/10.5281/zenodo.7877330)

ESPO-G6-E5L v1.0.0: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7764929.svg)](https://doi.org/10.5281/zenodo.7764929)




## Context
The need to adapt to climate change is present in a growing number of fields, leading to an increase in the demand for 
climate scenarios for often interrelated sectors of activity. In order to meet this growing demand and to ensure the 
availability of climate scenarios responding to numerous vulnerability, impact, and adaptation (VIA) studies, 
[Ouranos](https://www.ouranos.ca) is working to create a set of operational multipurpose climate scenarios called 
"Ensemble de Simulations Post-traitées d'Ouranos" (ESPO) covering North America at a resolution of 0.1°. 
In ESPO-G6-R2 v1.0.0, CMIP6 global climate models simulations are bias-adjusted using the RDRS v2.1 reference dataset.
The simulation ensemble covers the period for years 1950-2100 and includes the daily minimum temperature (`tasmin`), the daily maximum temperature (`tasmax`) and the daily mean precipitation flux (`pr`).
The experiments included are SSP2-4.5 and SSP3-7.0.


To avoid the "hot model problem" (Hausfather et al, 2022), only models with a Transient Climate Response (TCR) in the likely range (1.4–2.2 °C) were kept in the official ensemble (Table 1).
Extra "hot models" and SSP5-8.5 are also available even if they are not in the official ensemble.

**Table 1. Members of ESPO-G6-R2 v1.0.0**

|**Institution**|**Model** |**Member** |**License**|**TCR (degC)**|**In TCR likely range**|**Status**|
|---|---|---|---|---|---|---|
|CAS |	FGOALS-g3 |	r1i1p1f1 |CC BY 4.0|1.50|✓| Completed|
|CMCC 	|CMCC-ESM2 |	r1i1p1f1 |CC BY 4.0|1.92|✓|Completed|
|	CSIRO-ARCCSS |	ACCESS-CM2 |	r1i1p1f1  |CC BY 4.0|1.96|✓|Completed|
| CSIRO 	|ACCESS-ESM1-5 |	r1i1p1f1 |CC BY 4.0|1.97|✓|Completed|
| 	DKRZ |	MPI-ESM1-2-HR |	r1i1p1f1 |CC BY 4.0|1,64|✓|Completed|
| 	INM 	|INM-CM5-0 |	r1i1p1f1 |CC BY 4.0|1.41|✓|Completed|
| 	MIROC |	MIROC6 |	r1i1p1f1 |CC BY 4.0|1.55|✓|Completed|
| 	MPI-M |	MPI-ESM1-2-LR |	r1i1p1f1 |CC BY 4.0|1.82|✓|Completed|
| 	MRI |	MRI-ESM2-0 |	r1i1p1f1 |CC BY 4.0|1.67|✓|Completed|
| 	NCC |	NorESM2-LM |	r1i1p1f1 |CC BY 4.0|1.49|✓|Completed|
| 	CNRM-CERFACS |	CNRM-ESM2-1 |	r1i1p1f2 |CC BY 4.0|1.83|✓|Completed|
| 	NIMS-KMA |	KACE-1-0-G |	r1i1p1f1 |CC BY 4.0|2.04|✓|Completed|
| 	NOAA-GFDL |	GFDL-ESM4 |	r1i1p1f1 |CC BY 4.0|1.63|✓|Completed|
| 	BCC |	BCC-CSM2-MR |	r1i1p1f1 |CC BY 4.0|1.55|✓|Completed|
| AS-RCEC	 |	TaiESM1 |	r1i1p1f1 |CC BY 4.0|2.27| |Completed|
| CCCma	 |	CanESM5 |	r1i1p1f1 |CC BY 4.0|2.71| |Completed|
| CNRM-CERFACS	 |	CNRM-CM6-1 |r1i1p1f2	 |CC BY 4.0|2.22| |Completed|
| EC-Earth-Consortium	 |	EC-Earth3 |r1i1p1f1	 |CC BY 4.0|2.30| |Completed|
| IPSL	 |	IPSL-CM6A-LR |	r1i1p1f1 |CC BY 4.0|2.35| |Completed|
| 	MOHC |	UKESM1-0-LL |	r1i1p1f2 |CC BY 4.0|2.77| |Completed|
| 	NCC |NorESM2-MM	 |	r1i1p1f1 |CC BY 4.0|1.22| |Completed|
| EC-Earth-Consortium	 |	EC-Earth3-CC  |r1i1p1f1	 |CC BY 4.0|2.63| |Completed (only SSP2-4.5)|
| 	NUIST |NESM3 	 |	r1i1p1f1 |CC BY 4.0|2.72| |Completed (only SSP2-4.5)|
| 	MIROC |MIROC-ES2L	 |	r1i1p1f2 |CC BY 4.0|1.49| ✓|Planned|
| 	EC-Earth-Consortium |EC-Earth3-Veg	 |	r1i1p1f1 |CC BY 4.0|2.66| |Planned|
| 	INM |INM-CM4-8	 |	r1i1p1f1 |CC BY 4.0|1.30| |Planned|
| CCCma	 |	CanESM5-1 |	r1i1p1f1 |CC BY 4.0| | ?|Planned|



Licences: https://wcrp-cmip.github.io/CMIP6_CVs/docs/CMIP6_source_id_licenses.html

TCR: Hausfather et al. 2022, Climate simulations: recognize the 'hot model' problem, comment in Nature: [DOI: 10.5281/zenodo.6476375](https://doi.org/10.5281/zenodo.6476375)

## Spatial coverage
The dataset has a resolution of 0.1° over a North American domain on a rotated grid with
a grid pole latitude of 31.7583 and longitude of 87.5970. The latitude range covered is 
from 5.7560°N to 83.9816°N and the longitude range is from 179.9728°E to 9.0204°W.

> :warning: Users should be careful with precipitation data close to the south edge of the domain where there is less trust in the reference data.

Data is only available on or near land. A mask was created by removing all grid cells that 
had a sea area fraction of 1 in the reference dataset and then putting back a buffer 
of one grid cell along the coasts.

Some small regions in Alaska and Greenland have been masked out by NaNs for 2 models.
More details are available in section 5 of [the documentation of the adjustment method.](documentation/ESPO_G6_R2v100_adjustment.pdf)

## Temporal coverage
As the bias-adjustment method requires a consistent number of calendar days (no leap days), all members using a standard
calendar were converted to the `noleap` one by dropping any values for February 29th. `KACE-1-0-G`
is the only model simulated with a 360-day calendar, and was kept as is.

The bias-adjustment was calibrated over the years 1989-2018, the most recont 30-year period available, and applied to the full 1950-2100 period.

## Reference data
The ESPO-G6-R2 v1.0.0 dataset uses the RDRS v2.1 (Gasset et al., 2021) as reference dataset. This is a product
from Environment and Climate Change Canada (ECCC) created by using the Regional 
Deterministic Reforecast System (RDRS) to downscale the Global Deterministic Reforecast 
System (GDRS) initialized by ERA-Interim. The system is also coupled with the Canadian 
Land Data Assimilation System (CaLDAS) and Precipitation Analysis (CaPA). It was downloaded from
[CaSPAR](https://caspar-data.ca).

> :warning: A different version of ESPO-G6 uses ERA5-Land as a reference. 
The information for ESPO-G6-E5L can be found in this [release](https://github.com/Ouranosinc/ESPO-G/releases/tag/v1.0.0) with [doi:10.5281/zenodo.7764929](https://zenodo.org/record/7764929#.ZEbAg3aZPz8).

## Methodology
The temperature and precipitation data from the simulations in Table 1 were first extracted over North America.
Then, all the extracted simulation data are interpolated bilinearly in cascades to the RDRS v2.1 grid. The ESPO-G6-R2 v.1.0.0 bias adjustment procedure then uses [xclim's bias adjustment algorithms](https://xclim.readthedocs.io/en/stable/sdba.html)
to adjust simulation bias following a quantile mapping procedure. In particular, the algorithm used is inspired by the
"Detrended Quantile Mapping" (DQM) method described by Cannon (2015). The procedure is bipartite;
First, the adjustment factors are calculated based on reference data and simulations over a common period (training stage),
and second, the entire simulation is corrected with these factors (adjustment step). The reference period chosen here were years 1989-2018.
Adjustments are univariate, where corrections are applied separately for each of the 3 variables. Data is adjusted for
each day of the year, using a rolling window of 31 days. Although computational more expensive, the rolling window method
allows for better adjustment of the annual cycle. Note that this method does not work well with leap years as there is four
(4) times fewer data values for day 366. To remedy this problem, all simulations as well as the reference product are
converted to this "noleap" calendar. A more detailed explanation of the adjustment process is given in [the documentation](documentation/ESPO_G6_R2v100_adjustment.pdf).

## Data processing tools
Production and regular updates of ESPO-R/G operational datasets represent a challenge in terms of computational resources. 
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

- `simulation.json` and `simulation.csv`: An intake-esm catalog, compatible with xscen, listing the daily simulation datasets to use as inputs.
- `reconstruction.json` and `reconstruction.csv`: An intake-esm catalog, compatible with xscen, listing the daily reference datasets to use as inputs.
- `paths.yml`: A yaml file with the paths needed by the workflows. `configuration/template_paths.yml` shows an example of such a file, one only needs to replace the placeholders.

To run the workflow, uncomment the tasks wanted at the top of config file. Then, run

``python workflow_ESPO-G.py``

Description of the tasks:
 - makeref: Create the reference dataset with the right domain, period and calendar.
 - extract: Extract the simulation dataset with the right domain and period. 
 - regrid: Regrid the simulation onto the reference grid.
 - rechunk: Rechunk the regridded dataset to prepare for the bias adjustment (needed on large datasets).
 - train: Train the bias adjustment algorithm.
 - adjust: Adjust the simulation dataset with the trained bias adjustment algorithm.
 - clean_up: Join each individually adjusted variable back in one scenario dataset and clean up other details.
 - final_zarr: Rechunk the scenario dataset and save it.
 - diagnostics: Compute simple diagnostics (defined in configuration/properties_ESPO-G.yml) on the whole domain for a quality check.
 - concat: Concatenate scenario and diagnostics of the three regions into the complete NAM domain.  
 - official-diag: Compute diagnostics (defined in configuration/off-properties_ESPO-G.yml) on smaller regions to assess the performance.
 - indicators: Compute indicators (defined in configuration/portraits.yml) on the scenario.
 - climatological_mean: Compute the climatological mean of the indicators.
 - delta: Compute the deltas of the climatological means.
 - ensemble: Compute the ensemble statistics.
 
Loop structure:
```
makeref
for sim in simulations: # iterate over all models and experiments
    # We split the domain in three in order to have less computationnaly expensive task.
    for region in regions: # iterate over 3 sub-regions of NAM. 
        extract
        regrid
        rechunk
        for var in variable:
            train
            adjust
        clean_up
        final_zarr
        diagnostics
    concat
    
# tasks below iterate inside the task
official diag
indicators
climatological_mean
delta
ensembles
```

## Performance
Bias-adjustment of climate simulations is a quest with many traps. In order to assess the improvements and regressions
that the process brought to the simulations, we emulated the "VALUE" validation framework (Maraun et al., 2015).
While that project aimed to "to validate and compare downscaling methods", we based our approach on its ideas of statistical
"properties" and "measures" to measure bias between the simulations, the scenarios, and the reference.

A detailed analysis is given in [the documentation](documentation/ESPO_G6_R2v100_performance.pdf).
Our general conclusions concerning the quality of ESPO-G6-R2 v1.0.0 are:

 - The marginal properties of the simulations (mean, quantiles) are very well-adjusted, by design of the Quantile Mapping algorithm.
 - The climate change signal is also conserved from the simulations by design of the algorithm.
 - A side effect of adjusting the distributions explicitly is the improvement of the inter-variable correlation, even though the bias correction algorithm does not aim to adjust these aspects.
 - Because tasmin is not directly adjusted, but rather computed from the adjusted tasmax and dtr, it seems that our diagnostics show weaker improvements, compared to tasmax.
 

## Data availability and download
The ESPO-G6-R2 v1.0.0 data is currently available under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.

At the time of publication, the data is stored on [Ouranos](https://www.ouranos.ca/)' THREDDS server, a part of the [PAVICS](https://pavics.ouranos.ca/) project:
https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/catalog/datasets/simulations/bias_adjusted/cmip6/ouranos/ESPO-G/ESPO-G6-R2v1.0.0/catalog.html

When new versions of ESPO-G will be released, previous versions may be pulled from the server. [Please contact us](mailto:scenarios@ouranos.ca) if you wish to obtain these.

## Acknowledgements
We acknowledge the World Climate Research Programme, which, through its Working Group on Coupled Modelling, coordinated and promoted CMIP6. We thank the climate modeling groups for producing and making available their model output, the Earth System Grid Federation (ESGF) for archiving the data and providing access, and the multiple funding agencies who support CMIP6 and ESGF.


## References
Cannon, A. J., Sobie, S. R., & Murdock, T. Q. (2015). Bias correction of GCM precipitation by quantile mapping: How well do methods preserve changes in quantiles and extremes? Journal of Climate, 28(17), 6938–6959. https://doi.org/10.1175/JCLI-D-14-00754.1

Gasset, N., Fortin, V., Dimitrijevic, M., Carrera, M., Bilodeau, B., Muncaster, R.,  Etienne Gaborit, Roy, G., Pentcheva, N., Bulat, M., Wang, X., Pavlovic, R., Lespinas, F., Khedhaouiria, D., (2021). A 10 km north american precipitation and land surface reanalysis based on the gem atmospheric model. Hydrology and Earth System Sciences. doi:10.5194/hess-2021-41.

Hausfather, Z., Marvel, K., Schmidt, G. A., Nielsen-Gammon, J. W., Zelinka, M. (2022). Climate simulations: recognize the ‘hot model’ problem. Nature 2022 605:7908, 605(7908), 26–29. https://doi.org/10.1038/d41586-022-01192-2

Logan, T., Bourgault, P., Smith, T. J., Huard, D., Biner, S., Labonté, M.-P., Rondeau-Genesse, G., Fyke, J., Aoun, A., Roy, P., Ehbrecht, C., Caron, D., Stephens, A., Whelan, C., Low, J.-F., Keel, T., Lavoie, J., Tanguy, M., Barnes, C., … Quinn, J. (2022). Ouranosinc/xclim (0.35.0) [Python]. Zenodo. https://doi.org/10.5281/zenodo.6407112

Maraun, D., Widmann, M., Gutiérrez,  J.M., Kotlarski, S., Chandler, R. E., Hertig, E., Wibig, J., Huth, R., Wilcke, R. A. I. (2015). VALUE: A Framework to Validate Downscaling Approaches for Climate Change Studies. Earth’s Future 3, 1, 1‑14. https://doi.org/10.1002/2014EF000259.

Zhuang, J., Dussin, R., Huard, D., Bourgault, P., Banihirwe, A., Raynaud, S., Malevich, B., Schupfner, M., Hamman, J., Levang, S., Jüling, A., Almansi, M., Fernandes, F., Rondeau-Genesse, G., Rasp, S., & Bell, R. (2021). pangeo-data/xESMF (0.6.2) [Python]. Zenodo. https://doi.org/10.5281/zenodo.5721118

