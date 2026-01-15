# ESPO6 : Ensemble de Simulations Post-traitées d’Ouranos -  CMIP6 / Ouranos Ensemble of Bias-adjusted Simulations - CMIP6


## Context and Data Description
The need to adapt to climate change is present in a growing number of fields, leading to an increase in the demand for climate scenarios for often interrelated sectors of activity. In order to meet this growing demand and to ensure the availability of climate scenarios responding to numerous vulnerability, impact, and adaptation (VIA) studies, 
[Ouranos](https://www.ouranos.ca) is working to create a set of operational multipurpose bias-adjusted climate simulations called "Ensemble de Simulations Post-traitées d'Ouranos" (ESPO).

ESPO6 v1.0 is described in the following article:
Lavoie et al., An ensemble of bias-adjusted CMIP6 climate simulations based on a high-resolution North American reanalysis. Nature Scientific Data. 10.1038/s41597-023-02855-z (2024).
https://www.nature.com/articles/s41597-023-02855-z

DOI for the code and data:[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7764928.svg)](https://doi.org/10.5281/zenodo.7764928)

The data is available on [PAVICS](https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/catalog/datasets/simulations/bias_adjusted/cmip6/ouranos/ESPO-G/catalog.html).

Dataset Characteristics:
* Temporal coverage: 1950-2100
* Temporal resolution: daily, noleap or 360_day calendar
* Spatial coverage: North American domain from 179.9°W to 10.0°W and from 10.0°N to 83.3°N, only on land.
* Spatial resolution: 0.1°
* Data type: Gridded netCDF
* License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)


## Versions

 ### v2.0
 
 Major changes:
 * Add hurs and hursTasmax
 * Add possibility to run until 2300
 * Add possibility to run ESPO-R
 * Fix bug on adapt freq (https://github.com/Ouranosinc/ESPO-G/issues/8)
 * Add CaSR v3.2 reference
 * Add sftlf mask for the simulation

Minor changes:
* KACE-1-0-G was excluded. (https://github.com/Ouranosinc/ESPO-G/issues/6)
* EC-Earth3-CC and NESM3 were excluded as they do not have SSP3-7.0 available.
* New calculation of the TCR lead to CNRM-CM6-1/INM-CM5-0  being included/excluded in the TCR likely range. (https://github.com/Ouranosinc/ESPO-G/issues/7)

- 2026-01: initial tests ran with xscen-0.13
- 2026-01-13: initial tests ran with espojan2026: xclim-0.59.2.dev4-py3-none-any.whl (main), xscen-0.13.2.dev4-py3-none-any.whl (add-nan-check),  xsdba-0.5.1.dev8-py3-none-any.whl (main).
 needed to revert to xscen-0.13 for some regrid.
 
#### Project lait-e
    
  Includes hurs and hursTasmax. Ran initial tests for lait-e in 2025-08 on narval with xclim-0.57.1.dev10, xscen-0.12.4.dev5 and xsdba 0.5.0 wheels and numpy 1.26.4 (env dqm-np2) using config_general-2100.yml and config_QC-E5L.yml.

#### Project post-2100

  Includes simulation that reach 2300. Ran in 2025-12 with common env xscen-0.13 and branch post-2100-narval.


### v1.0
In ESPO6 v1.0.0, CMIP6 global climate models simulations are bias-adjusted using the RDRS v2.1 and the ERA5-Land reference datasets. The simulation ensemble covers the period for years 1950-2100 and includes the daily minimum temperature (tasmin), the daily maximum temperature (tasmax) and the daily mean precipitation flux (pr). 

* References: 

  * Lavoie et al., An ensemble of bias-adjusted CMIP6 climate simulations based on a high-resolution North American reanalysis. Nature Scientific Data. 10.1038/s41597-023-02855-z (2024).
https://www.nature.com/articles/s41597-023-02855-z

  * ESPO-G6-R2 v1.0.0: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7877330.svg)](https://doi.org/10.5281/zenodo.7877330)

  * ESPO-G6-E5L v1.0.0: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7764929.svg)](https://doi.org/10.5281/zenodo.7764929)

* Data availability:

  At the time of publication, the data is stored on [Ouranos](https://www.ouranos.ca/)' THREDDS server, a part of the [PAVICS](https://pavics.ouranos.ca/) project:
https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/catalog/datasets/simulations/bias_adjusted/cmip6/ouranos/ESPO-G/catalog.html

  When new versions of ESPO6 will be released, previous versions may be pulled from the server. [Please contact us](mailto:scenarios@ouranos.ca) if you wish to obtain these.

#### Project ESPO-G6-AHCCD

  Paper coming soon.



## Members
To avoid the "hot model problem" (Hausfather et al, 2022), only models with a Transient Climate Response (TCR) in the likely range (1.4–2.2 °C) were kept in the official ensemble (Table 1). The experiments in the official ensemble included are SSP2-4.5 and SSP3-7.0.
Extra "hot models" and SSP5-8.5 are also available even if they are not in the official ensemble.

**Table 1. Members of ESPO6 v2.0.0**

|**Model** |**Member** |**TCR (degC)**|**In TCR likely range**|**Status**|
|---|---|---|---|---|
| ACCESS-CM2     |r1i1p1f1| 2.1 | ✓ |not started|
| ACCESS-ESM1-5  |r1i1p1f1| 1.95 | ✓ |not started|
| BCC-CSM2-MR    |r1i1p1f1| 1.72 | ✓ |not started|
| CMCC-ESM2     |r1i1p1f1| 1.92* | ✓ |not started|
| CNRM-CM6-1     |r1i1p1f1| 2.14 | ✓ |not started|
| CNRM-ESM2-1    |r1i1p1f1| 1.86 | ✓ |not started|
| FGOALS-g3      |r1i1p1f1| 1.54 | ✓ |not started|
| GFDL-ESM4      |r1i1p1f1| 1.61 | ✓ |not started|
| MIROC-ES2L     |r1i1p1f1| 1.55 | ✓ |not started|
| MIROC6         |r1i1p1f1| 1.55 | ✓ |not started|
| MPI-ESM1-2-HR  |r1i1p1f1| 1.66 | ✓ |not started|
| MPI-ESM1-2-LR  |r1i1p1f1| 1.84 | ✓ |not started|
| MRI-ESM2-0     |r1i1p1f1| 1.64 | ✓ |not started|
| NorESM2-LM     |r1i1p1f1| 1.48 | ✓ |not started|
| CanESM5        |r1i1p1f1| 2.74 | x |not started|
| CanESM5-1      |r1i1p2f1| ? | x |not started|
| EC-Earth3      |r1i1p1f1| 2.3 | x |not started|
| EC-Earth3-Veg  |r1i1p1f1| 2.62 | x |not started|
| INM-CM4-8      |r1i1p1f1| 1.33 | x |not started|
| INM-CM5-0      |r1i1p1f1| 1.37 | x |not started|
| IPSL-CM6A-LR   |r1i1p1f1| 2.32 | x |not started|
| NorESM2-MM     |r1i1p1f1| 1.33 | x |not started|
| TaiESM1        |r1i1p1f1| 2.36 | x |not started|
| UKESM1-0-LL    |r1i1p1f1| 2.79 | x |not started|


Licences: All members have a CC BY 4.0 license. https://wcrp-cmip.github.io/CMIP6_CVs/docs/CMIP6_source_id_licenses.html

TCR: Computed using ESMValTool (https://docs.esmvaltool.org/en/latest/recipes/recipe_tcr.html), as done in the IPCC AR6. A previous version of this table used Hausfather et al. 2022, Climate simulations: recognize the 'hot model' problem, comment in Nature: [DOI: 10.5281/zenodo.6476375](https://doi.org/10.5281/zenodo.6476375) and gave slightly different results.   See https://github.com/Ouranosinc/ESPO-G/issues/7 for discussion.
*Note that the CMCC-ESM2 TCR is not available with the ESMValTool method. We show the one from Hausfather et al. (2022) instead.



## Instructions for the code

This version of the workflow is meant to be run on a HPC such as Narval. It uses the workflow manager software Snakemake.

To run the workflow:

1) On narval, activate the  virtual env:

```bash
$ pyact xscen-0.13
```

2) Specify the output files wanted in the rule `all:input` of the `Snakefile`. (Final files are input of checks and diagnostics. Hence, no need to explicitely ask for them, they will be created.)

3) Specify the simulations and reference wanted in `config/config_general.yml` and  `config/config_region.yml`.

4) Create your own `paths.yml` based on `paths-template.yml`.

5) If needed, personalize the `simple/config.v8+.yaml` for the right slurm parameters.

6) Run the workflow:

```bash
$ snakemake --profile simple
```

Snakemake should build a dag that looks like: ![Texte alternatif](dag.png)

Description of the tasks:
 - makeref: Create the reference dataset with the right domain, period and calendar.
 - ref-subregion: Divide the reference in region to be able to run in parallel.
 - extract: Extract the simulation dataset with the right domain and period. 
 - regrid: Regrid the simulation onto the reference grid.
 - rechunk: Rechunk the regridded dataset to prepare for the bias adjustment (needed on large datasets).
 - train: Train the bias adjustment algorithm.
 - adjust: Adjust the simulation dataset with the trained bias adjustment algorithm.
 - clean_up: Join each individually adjusted variable back in one scenario dataset and clean up other details.
 - concat: Concatenate adjusted simulation of the three regions into the complete NAM domain.  
 - diag: Compute diagnostics (defined in configuration/properties.yml) on smaller regions to assess the performance.



## Warnings

### Problematic Areas
 - Users should be careful with precipitation data close to the south edge of the North American domain where there is less trust in the reference data, especially for precipitations.
 -[TODO: verify for v2.0] Some small regions in Alaska and Greenland showed very small tasmin and have been masked out by NaNs for 2 models (BCC-CSM2-MR and GFDL-ESM4 ). More details are available in section Health Checks of Lavoie et al. (2024)

