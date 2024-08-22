from pathlib import Path

home=Path(config["paths"]["home"]) # needed because scripts looks in workflow/rules
ref_source = [config['extraction']['reference']['search_data_catalogs']['other_search_criteria']['source']]



rule off_diag_ref_prop:
    input:
        inp=official_diags_inputfiles_ref 
    output:
        prop= directory(expand(finaldir/"diagnostics/{{diag_domain}}/{ref_source}+{{diag_domain}}+diag_ref_prop.zarr", ref_source=ref_source)[0])
    params:
        n_workers=3,
        mem='60GB',
        cpus_per_task=15,
        step= "ref"
    script:
        home/"workflow/scripts/off_diag.py"

rule off_diag_sim_prop_meas:
    input:
        inp = official_diags_inputfiles_sim, 
        diag_ref_prop = expand(finaldir/"diagnostics/{{diag_domain}}/{ref_source}+{{diag_domain}}+diag_ref_prop.zarr",ref_source=ref_source)[0]
    output:
        prop= directory(finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_sim_prop.zarr"),
        meas= directory(finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_sim_meas.zarr")
    params:
        n_workers=3,
        mem='60GB',
        cpus_per_task=15,
        step= "sim"
    script:
        home/"workflow/scripts/off_diag.py"

rule off_diag_scen_prop_meas:
    input:
        inp = finaldir/"FINAL/NAM/day+{sim_id}+NAM_1950-2100.zarr",
        diag_ref_prop = expand(finaldir/"diagnostics/{{diag_domain}}/{ref_source}+{{diag_domain}}+diag_ref_prop.zarr",ref_source=ref_source)[0],
    output:
        prop= directory(finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_scen_prop.zarr"),
        meas= directory(finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_scen_meas.zarr")
    params:
        n_workers=3,
        mem='60GB',
        cpus_per_task=15,
        step= "scen"
    script:
        home/"workflow/scripts/off_diag.py"

rule diag_measures_improvement:
    input:
        sim=finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_sim_meas.zarr",
        scen=finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_scen_meas.zarr"
    output:
        finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+improvement.zarr"
    params:
        n_workers=3,
        mem='6GB',
        cpus_per_task=15,
    script:
        home/"workflow/scripts/diag_measures_improvement.py"