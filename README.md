# ESPO6 : Ensemble de Simulations Post-traitées d’Ouranos -  CMIP6 / Ouranos Ensemble of Bias-adjusted Simulations - CMIP6

This release is ESPO6 v2.0.

## Context
The need to adapt to climate change is present in a growing number of fields, leading to an increase in the demand for climate scenarios for often interrelated sectors of activity. In order to meet this growing demand and to ensure the availability of climate scenarios responding to numerous vulnerability, impact, and adaptation (VIA) studies, 
[Ouranos](https://www.ouranos.ca) is working to create a set of operational multipurpose bias-adjusted climate simulations called "Ensemble de Simulations Post-traitées d'Ouranos" (ESPO). ESPO6 v1.0 is described in the following article:
Lavoie et al., An ensemble of bias-adjusted CMIP6 climate simulations based on a high-resolution North American reanalysis. Nature Scientific Data. 10.1038/s41597-023-02855-z (2024). https://www.nature.com/articles/s41597-023-02855-z

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


## Versions

 ### v2.0 [This release]
 
 Changes from v1.0:
  * Add possibility to run hurs and hursTasmax
  * Add possibility to run until 2300
  * Add possibility to run for regional climate models
  * Fix bug on adapt freq (https://github.com/Ouranosinc/ESPO-G/issues/8)
  * Add CaSR v3.2 reference
  * Workflow uses snakemake
  * Add mask based in sftlf on the simulation
  * KACE-1-0-G was excluded. (https://github.com/Ouranosinc/ESPO-G/issues/6)
  * EC-Earth3-CC and NESM3 were excluded as they do not have SSP3-7.0 available.
  * New calculation of the TCR lead to CNRM-CM6-1/INM-CM5-0  being included/excluded in the TCR likely range. (https://github.com/Ouranosinc/ESPO-G/issues/7)  

  For ESPO-R:
  * Regrid in a single step
  * Start in 1951 (CRCM5 not available in 1950)
  * Fill in nans
  * Add spatial subset of input domain.
  * NAM domain slightly changed

Branch: snakemake

History:
  2026-01: ran ESPO-R-DQM and ESPO-R-Scaling with env espojan2026 
  2026-02: ran tests with env espojan2026. [ESPO-R-EV (bug, give up, Eric is working on it), ESPO-R-DQM-100 (works, this still has exploding pr), ESPO-R-DQM-tasmin (works, +s and -s vs DTR), ESPO-R-filter]
  2026-02: Create env espofev2026 to add xesmf 0.9.2 and xscen-0.13.2.dev7. Ran tests for ESPO-R-filter and redo ESPO-R-tasmin without bug

### Project lait-e

 Changes from v1.0:
 * Includes hurs and hursTasmax.
 * Fix bug on adapt freq (https://github.com/Ouranosinc/ESPO-G/issues/8)
 * CaSR v3.2 and ERA5-Land reference
 * Quebec domain only
 * Workflow uses snakemake
 * Includes all CMIP6 models that have hurs and hursTasmax
 * KACE-1-0-G was excluded. (https://github.com/Ouranosinc/ESPO-G/issues/6)
 * EC-Earth3-CC and NESM3 were excluded as they do not have SSP3-7.0 available.
 * New calculation of the TCR lead to CNRM-CM6-1/INM-CM5-0  being included/excluded in the TCR likely range. (https://github.com/Ouranosinc/ESPO-G/issues/7)

  Branch: lait-e
  
  History:   
    2025-10-30: Ran with env xscen-0.13 env for lait-E5L. 
    2026-01-06: Ran with env xscen-0.13 env for lait-E5L newly available models.
    2026-02-03: Ran with env xscen-0.13 env for lait-C3.


### ESPO-G6-C3-P2100 v1

ESPO-G6-C3-P2100 is a small ensemble of CMIP6 simulations extending to 2300 with variables for minimum daily temperature, maximum daily temperature and daily precipitation (tasmin, tasmax, pr). Beyond the ensemble composition, the main difference with ESPO6 v1 is the reference dataset, updated to the latest version of the Canadian Surface Reanalysis (CaSR v3.2).

Changes from ESPO6 v1.0:

* Covers the period from 1950 to 2300;
* Reference dataset updated from CaSR v2.1 to CaSR v3.2;
* Fix bug on adapt freq (https://github.com/Ouranosinc/ESPO-G/issues/8)
* Workflow executed using [snakemake](https://snakemake.readthedocs.io/)
* Data is available on PAVICS: TODO.

Branch: `post-2100-narval`
  
History: Ran in 2025-12 within conda environment `xscen-0.13`.

### ESPO-G6-AHCCD v1

ESPO-G6-AHCCD is a large ensemble of CMIP6 simulations over the period 1950–2100 bias-adjusted using station records from the _Adjusted and homogenized Canadian climate data_ (AHCCD v3). It includes total daily precipitation, minimum, maximum and mean daily temperature. One notable feature of this dataset is that it includes 627 simulations for precipitation and 561 for temperature.  

Changes from ESPO6 v1.0:
  
* Reference dataset is AHCCD v3, so projections are at the point scale;
* Data is available in Zarr format on the [PAVICS MinIO server](https://minio.ouranos.ca/) in the `portail-ing` bucket. It can be accessed programmatically using the S3 standard, see [documentation](https://github.com/Ouranosinc/peach) for tutorials.

References:

 * Huard, David, Sarah-Claude Bourdeau-Goulet, Léa Braschi, et al. 2026. “Delivering Probabilistic Climate Hazards Assessments.” Environmental Research Communications, ahead of print. https://doi.org/10.1088/2515-7620/ae3a4d.
 * Bourdeau-Goulet, Sarah-Claude, Pascal Bourgault, Sarah Gammon, and David Huard. 2025. Ouranos Ensemble of Bias-Adjusted Simulations - Global Models CMIP6 - AHCCD v3 (ESPO-G6-AHCCD v1.0.0). May 31. https://doi.org/10.20383/103.01272.

### v1.0
In ESPO6 v1.0.0, CMIP6 global climate models simulations are bias-adjusted using the RDRS v2.1 and the ERA5-Land reference datasets. The simulation ensemble covers the period for years 1950-2100 and includes the daily minimum temperature (tasmin), the daily maximum temperature (tasmax) and the daily mean precipitation flux (pr). 

Dataset Characteristics:
* Temporal coverage: 1950-2100
* Temporal resolution: daily, noleap or 360_day calendar
* Spatial coverage: North American domain from 179.9°W to 10.0°W and from 10.0°N to 83.3°N, only on land.
* Spatial resolution: 0.1°
* Data type: Gridded netCDF
* License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

* References: 

  * Lavoie et al., An ensemble of bias-adjusted CMIP6 climate simulations based on a high-resolution North American reanalysis. Nature Scientific Data. 10.1038/s41597-023-02855-z (2024).
https://www.nature.com/articles/s41597-023-02855-z

  * ESPO-G6-R2 v1.0.0: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7877330.svg)](https://doi.org/10.5281/zenodo.7877330)

  * ESPO-G6-E5L v1.0.0: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7764929.svg)](https://doi.org/10.5281/zenodo.7764929)

* Data availability:

  At the time of publication, the data is stored on [Ouranos](https://www.ouranos.ca/)' THREDDS server, a part of the [PAVICS](https://pavics.ouranos.ca/) project:
https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/catalog/datasets/simulations/bias_adjusted/cmip6/ouranos/ESPO-G/catalog.html

  When new versions of ESPO6 will be released, previous versions may be pulled from the server. [Please contact us](mailto:scenarios@ouranos.ca) if you wish to obtain these.




## Instructions for the code

This version of the workflow is meant to be run on a HPC such as Narval. It uses the workflow manager software Snakemake.

To run the workflow:

1) On narval, activate the  virtual env:

```bash
$ pyact xscen-0.13
```

2) Specify the output files wanted in the rule `all:input` of the `Snakefile`. (Final files are input of checks and diagnostics. Hence, no need to explicitely ask for them, they will be created.)

3) Specify the simulations and reference wanted in a config file in the directory `config/` and put its name at the top of the Snakemake file.

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

