# ESPO6 : Ensemble de Simulations Post-traitées d’Ouranos -  CMIP6 / Ouranos Ensemble of Bias-adjusted Simulations - CMIP6

This release is for Project post-2100.

The data is available on PAVICS: COMING SOON.

The data is described in  COMING SOON.

## Context and Data Description
The need to adapt to climate change is present in a growing number of fields, leading to an increase in the demand for climate scenarios for often interrelated sectors of activity. In order to meet this growing demand and to ensure the availability of climate scenarios responding to numerous vulnerability, impact, and adaptation (VIA) studies, 
[Ouranos](https://www.ouranos.ca) is working to create a set of operational multipurpose bias-adjusted climate simulations called "Ensemble de Simulations Post-traitées d'Ouranos" (ESPO). ESPO6 v1.0 is described in the following article:
Lavoie et al., An ensemble of bias-adjusted CMIP6 climate simulations based on a high-resolution North American reanalysis. Nature Scientific Data. 10.1038/s41597-023-02855-z (2024). https://www.nature.com/articles/s41597-023-02855-z

## Versions

### Project ESPO-G6-C3-P2100 [This release]
Post-2100 simulations.

 Changes from v1.0:
 * Run until 2300.
 * Fix bug on adapt freq (https://github.com/Ouranosinc/ESPO-G/issues/8)
 * CaSR v3.2 reference
 * Workflow uses snakemake
 * Includes all CMIP6 models and experiment that went post-2100.

  Branch: post-2100-narval
  
  History: Ran in 2025-12 with common env xscen-0.13

### Project ESPO-G6-AHCCD

  Similar to v1 but reference is AHCCD.
  
  Paper coming soon.

  Reference: https://www.frdr-dfdr.ca/repo/dataset/876e9380-63fc-4eaa-987b-aa16c3770941

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

1)
 For Ouranos employee:
On narval, activate the virtual env :

```bash
$ pyact xscen-0.13
```
For everybody else (with a narval account):
Create a virtual env and activate it.

```bash
# activate modules
$ module load StdEnv/2023 gcc openmpi python/3.13 arrow proj/9.2 geos/3.12 mpi4py/3 netcdf geos nodejs esmf/8.8

# create virtual env. Replace <ENV> by the name of your env
$ virtualenv --no-download <ENV>

# activate env
$ source <ENV>/bin/activate

# install requirements
$ pip install --no-index --upgrade pip
$ pip install --no-index -r requirements.txt
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

