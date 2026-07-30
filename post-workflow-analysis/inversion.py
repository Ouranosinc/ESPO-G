"""Count the temperature inversions before the swap."""

from pathlib import Path

import xarray as xr
import xscen as xs
from xscen import CONFIG


xs.load_config(
    "../config/ARCHES/config_ARCHES.yml",
    "../config/ARCHES/paths_ARCHES.yml",
    reset=True,
)
cat = xs.ProjectCatalog(f"{CONFIG['arches']}/cat_ARCHES.json")
ids = [
    "CMIP6_ScenarioMIP_INM_INM-CM5-0_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_INM_INM-CM5-0_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_INM_INM-CM5-0_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_INM_INM-CM5-0_ssp370_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_INM_INM-CM5-0_ssp370_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_INM_INM-CM5-0_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_INM_INM-CM5-0_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_INM_INM-CM4-8_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_INM_INM-CM4-8_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_INM_INM-CM4-8_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp585_r8i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp585_r4i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp585_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp585_r2i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp585_r3i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp245_r4i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp245_r8i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp245_r3i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp245_r2i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp245_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp370_r2i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp370_r3i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp370_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp370_r4i1p1f2_global",
    "CMIP6_ScenarioMIP_MOHC_UKESM1-0-LL_ssp370_r8i1p1f2_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp585_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp585_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp585_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp585_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp245_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp245_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp370_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp370_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_MPI-M_MPI-ESM1-2-LR_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_AS-RCEC_TaiESM1_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CMCC_CMCC-ESM2_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CMCC_CMCC-ESM2_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CMCC_CMCC-ESM2_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CAS_FGOALS-g3_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CAS_FGOALS-g3_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_CAS_FGOALS-g3_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CAS_FGOALS-g3_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CAS_FGOALS-g3_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CAS_FGOALS-g3_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CAS_FGOALS-g3_ssp585_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp585_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp585_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp245_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp245_r6i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp245_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp370_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp370_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp370_r6i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO_ACCESS-ESM1-5_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_NCC_NorESM2-MM_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_NCC_NorESM2-MM_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_NCC_NorESM2-MM_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_NCC_NorESM2-MM_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_NCC_NorESM2-LM_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_NCC_NorESM2-LM_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_NCC_NorESM2-LM_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_NCC_NorESM2-LM_ssp245_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_NCC_NorESM2-LM_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_NOAA-GFDL_GFDL-ESM4_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_NOAA-GFDL_GFDL-ESM4_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_NOAA-GFDL_GFDL-ESM4_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp585_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp585_r1i2p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp585_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp585_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp370_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp370_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp245_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_MRI_MRI-ESM2-0_ssp245_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp585_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp585_r6i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp585_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp585_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp370_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp370_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp245_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp245_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_IPSL_IPSL-CM6A-LR_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC-ES2L_ssp585_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC-ES2L_ssp585_r2i1p1f2_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC-ES2L_ssp245_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC-ES2L_ssp245_r2i1p1f2_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC-ES2L_ssp370_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC-ES2L_ssp370_r2i1p1f2_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp370_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp370_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp245_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp245_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp585_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp585_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp585_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_MIROC_MIROC6_ssp585_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp370_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp370_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp245_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp245_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp585_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp585_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp585_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CSIRO-ARCCSS_ACCESS-CM2_ssp585_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_CNRM-CERFACS_CNRM-CM6-1_ssp585_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_CNRM-CERFACS_CNRM-CM6-1_ssp370_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_CNRM-CERFACS_CNRM-CM6-1_ssp245_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_CNRM-CERFACS_CNRM-ESM2-1_ssp245_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_CNRM-CERFACS_CNRM-ESM2-1_ssp370_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_CNRM-CERFACS_CNRM-ESM2-1_ssp585_r1i1p1f2_global",
    "CMIP6_ScenarioMIP_DKRZ_MPI-ESM1-2-HR_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_DKRZ_MPI-ESM1-2-HR_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_DKRZ_MPI-ESM1-2-HR_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_DKRZ_MPI-ESM1-2-HR_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_DKRZ_MPI-ESM1-2-HR_ssp370_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_DKRZ_MPI-ESM1-2-HR_ssp370_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_DKRZ_MPI-ESM1-2-HR_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_DKRZ_MPI-ESM1-2-HR_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp585_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp585_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp585_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp585_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp585_r1i1p2f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp370_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp370_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp370_r1i1p2f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp370_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp245_r5i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp245_r3i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp245_r1i1p2f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5_ssp245_r2i1p1f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5-1_ssp585_r1i1p2f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5-1_ssp370_r1i1p2f1_global",
    "CMIP6_ScenarioMIP_CCCma_CanESM5-1_ssp245_r1i1p2f1_global",
    "CMIP6_ScenarioMIP_BCC_BCC-CSM2-MR_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_BCC_BCC-CSM2-MR_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_BCC_BCC-CSM2-MR_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3-Veg_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3-Veg_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3-Veg_ssp245_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3-Veg_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3-Veg_ssp585_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3-Veg_ssp585_r6i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3-Veg_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp585_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp585_r6i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp585_r9i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp585_r11i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp585_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp370_r1i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp370_r6i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp370_r11i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp370_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp370_r9i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp245_r6i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp245_r9i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp245_r4i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp245_r11i1p1f1_global",
    "CMIP6_ScenarioMIP_EC-Earth-Consortium_EC-Earth3_ssp245_r1i1p1f1_global",
    "CMIP6_CORDEX_CNRM-ESM2-1_r1i1p1f2_OURANOS_CRCM5-SN_ssp245_r1_NAM-12",
    "CMIP6_CORDEX_CNRM-ESM2-1_r1i1p1f2_OURANOS_CRCM5-SN_ssp370_r1_NAM-12",
    "CMIP6_CORDEX_CanESM5_r1i1p2f1_OURANOS_CRCM5-SN_ssp585_r1_NAM-12",
    "CMIP6_CORDEX_CanESM5_r1i1p2f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12",
    "CMIP6_CORDEX_CanESM5_r1i1p2f1_OURANOS_CRCM5-SN_ssp245_r1_NAM-12",
    "CMIP6_CORDEX_NorESM2-MM_r1i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12",
    "CMIP6_CORDEX_NorESM2-MM_r1i1p1f1_OURANOS_CRCM5-SN_ssp245_r1_NAM-12",
    "CMIP6_CORDEX_MPI-ESM1-2-LR_r5i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12",
    "CMIP6_CORDEX_MPI-ESM1-2-LR_r4i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12",
    "CMIP6_CORDEX_MPI-ESM1-2-LR_r1i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12",
    "CMIP6_CORDEX_MPI-ESM1-2-LR_r3i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12",
    "CMIP6_CORDEX_MPI-ESM1-2-LR_r2i1p1f1_OURANOS_CRCM5-SN_ssp370_r1_NAM-12",
    "CMIP6_CORDEX_MPI-ESM1-2-LR_r1i1p1f1_OURANOS_CRCM5-SN_ssp245_r1_NAM-12",
]


if __name__ == "__main__":
    # if not Path(f"{CONFIG['arches']}/inversion").exists():
    #     Path(f"{CONFIG['arches']}/inversion").mkdir(parents=True, exist_ok=True)

    # for sim_id in ids:
    #     if "ssp370" in sim_id:
    #         # original dtr to find mask of inversions.
    #         dtrpreswap = xr.open_zarr(
    #             f"{CONFIG['espo']}/preswap/dtrpreswap_day_ESPO6_v20_CaSR+{sim_id}_NAM.zarr.zip"
    #         )
    #         dtrpreswap = dtrpreswap.convert_calendar(
    #             calendar="standard", use_cftime=False, align_on="year"
    #         )
    #         swap = (dtrpreswap < 0).resample(time="QS-DEC").sum()
    #         swap = swap.sel(time=slice("1951-01", "2099-11"))
    #         swap = xs.utils.unstack_dates(swap).expand_dims(realization=[sim_id])
    #         total = dtrpreswap.resample(time="QS-DEC").count()
    #         total = total.sel(time=slice("1951-01", "2099-11"))
    #         total = xs.utils.unstack_dates(total).expand_dims(realization=[sim_id])
    #         if not Path(
    #             f"{CONFIG['arches']}/inversion/ds_total_{sim_id}.zarr.zip"
    #         ).exists():
    #             xs.save_to_zarr(
    #                 swap,
    #                 f"{CONFIG['arches']}/inversion/ds_swap_{sim_id}.zarr.zip",
    #                 zip_zarrdir="${SLURM_TMPDIR}",
    #             )
    #             xs.save_to_zarr(
    #                 total,
    #                 f"{CONFIG['arches']}/inversion/ds_total_{sim_id}.zarr.zip",
    #                 zip_zarrdir="${SLURM_TMPDIR}",
    #             )
    # swaps = []
    # totals = []
    # for sim_id in ids:
    #     if "ssp370" in sim_id:
    #         swap = xr.open_zarr(
    #             f"{CONFIG['arches']}/inversion/ds_swap_{sim_id}.zarr.zip"
    #         )
    #         swaps.append(swap)
    #         total = xr.open_zarr(
    #             f"{CONFIG['arches']}/inversion/ds_total_{sim_id}.zarr.zip"
    #         )
    #         totals.append(total)

    # ds_swap = xr.concat(swaps, dim="realization")
    # ds_total = xr.concat(totals, dim="realization")

    # p = f"{CONFIG['arches']}/inversion/ds_swap.zarr.zip"
    # if not Path(p).exists():
    #     xs.save_to_zarr(
    #         ds_swap,
    #         p,
    #         zip_zarrdir="${SLURM_TMPDIR}",
    #     )
    # p = f"{CONFIG['arches']}/inversion/ds_total.zarr.zip"
    # if not Path(p).exists():
    #     xs.save_to_zarr(
    #         ds_total,
    #         p,
    #         zip_zarrdir="${SLURM_TMPDIR}",
    #     )

    ds_swap = xr.open_zarr(f"{CONFIG['arches']}/inversion/ds_swap.zarr.zip")
    ds_total = xr.open_zarr(f"{CONFIG['arches']}/inversion/ds_total.zarr.zip")
    for i, season in enumerate(["DJF", "MAM", "JJA", "SON"]):
        for j, period in enumerate([["1991", "2020"], ["2071", "2100"]]):
            curswap = ds_swap.sel(time=slice(*period), season=season).sum(
                dim=["time", "realization"]
            )
            curtotal = ds_total.sel(time=slice(*period), season=season).sum(
                dim=["time", "realization"]
            )
            frac = curswap / curtotal
            frac.dtr.attrs["long_name"] = "fraction of inversions"
            del frac.dtr.attrs["units"]
            p = f"{CONFIG['arches']}/inversion/frac_{season}_{period[0]}.zarr.zip"
            if not Path(p).exists():
                xs.save_to_zarr(
                    frac,
                    p,
                    zip_zarrdir="${SLURM_TMPDIR}",
                )
