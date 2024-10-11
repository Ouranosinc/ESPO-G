from pathlib import Path

home=Path(config["paths"]["home"]) # needed because scripts looks in workflow/rules
ref_source = [config['extraction']['reference']['search_data_catalogs']['other_search_criteria']['source']]
tmpdir= Path(config['paths']['tmpdir'])


rule off_diag_ref_prop:
    input:
        inp=official_diags_inputfiles_ref 
    output:
        prop= temp(directory(expand(tmpdir/"{ref_source}+{{diag_domain}}+diag_ref_prop.zarr", ref_source=ref_source)[0]))
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
        diag_ref_prop = expand(finaldir/"diagnostics/{{diag_domain}}/{ref_source}+{{diag_domain}}+diag_ref_prop.zarr.zip", ref_source=ref_source)[0]
    output:
        prop= temp(directory(tmpdir/"{sim_id}+{diag_domain}+diag_sim_prop.zarr")),
        meas= temp(directory(tmpdir/"{sim_id}+{diag_domain}+diag_sim_meas.zarr"))
    params:
        n_workers=3,
        mem='60GB',
        cpus_per_task=15,
        step= "sim"
    script:
        home/"workflow/scripts/off_diag.py"

rule off_diag_scen_prop_meas:
    input:
        inp = finaldir/"final/NAM/day+{sim_id}+NAM_1950-2100.zarr.zip",
        diag_ref_prop = expand(finaldir/"diagnostics/{{diag_domain}}/{ref_source}+{{diag_domain}}+diag_ref_prop.zarr.zip", ref_source=ref_source)[0],
    output:
        prop= temp(directory(tmpdir/"{sim_id}+{diag_domain}+diag_scen_prop.zarr")),
        meas= temp(directory(tmpdir/"{sim_id}+{diag_domain}+diag_scen_meas.zarr"))
    params:
        n_workers=3,
        mem='60GB',
        cpus_per_task=15,
        step= "scen"
    script:
        home/"workflow/scripts/off_diag.py"

rule diag_measures_improvement:
    input:
        sim=tmpdir/"{sim_id}+{diag_domain}+diag_sim_meas.zarr",
        scen=tmpdir/"{sim_id}+{diag_domain}+diag_scen_meas.zarr"
    output:
        temp(directory(tmpdir/"{sim_id}+{diag_domain}+improvement.zarr"))
    params:
        n_workers=3,
        mem='6GB',
        cpus_per_task=15,
    script:
        home/"workflow/scripts/off_diag_improvement.py"


rule move_ref:
    input:
        prop_ref=expand(tmpdir/"{ref_source}+{{diag_domain}}+diag_ref_prop.zarr", ref_source=ref_source)[0],
    output:
        prop_ref=expand(finaldir/"diagnostics/{{diag_domain}}/{ref_source}+{{diag_domain}}+diag_ref_prop.zarr.zip", ref_source=ref_source)[0],
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
    script:
        home/"workflow/scripts/move.py"

rule move_diag:
    input:
        prop_sim=tmpdir/"{sim_id}+{diag_domain}+diag_sim_prop.zarr",
        meas_sim=tmpdir/"{sim_id}+{diag_domain}+diag_sim_meas.zarr",
        prop_scen=tmpdir/"{sim_id}+{diag_domain}+diag_scen_prop.zarr",
        meas_scen=tmpdir/"{sim_id}+{diag_domain}+diag_scen_meas.zarr",
        imp=tmpdir/"{sim_id}+{diag_domain}+improvement.zarr",
    output:
        prop_sim=finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_sim_prop.zarr.zip",
        meas_sim=finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_sim_meas.zarr.zip",
        prop_scen=finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_scen_prop.zarr.zip",
        meas_scen=finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+diag_scen_meas.zarr.zip",
        imp=finaldir/"diagnostics/{diag_domain}/{sim_id}+{diag_domain}+improvement.zarr.zip",
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
    script:
       home/"workflow/scripts/move.py"