from pathlib import Path


region_name=list(config["custom"]["regions"].keys())
ref_source = [config['extraction']['reference']['search_data_catalogs']['other_search_criteria']['source']]
finaldir=Path(config['paths']['final'])
home=Path(config["paths"]["home"]) # needed because scripts looks in workflow/rules


rule ref_default:
    output:
        directory(finaldir/"reference/{ref_source}+{region}+default.zarr")
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
    script:
        home/"workflow/scripts/ref_default.py"

rule reference_calendar:
    input:
        finaldir/"reference/{ref_source}+{region}+default.zarr"
    output:
        directory(finaldir/"reference/{ref_source}+{region}+{calendar}.zarr")
    params:
        n_workers=2,
        mem='50GB',
        cpus_per_task=10,
    script:
        home/"workflow/scripts/ref_calendar.py"
        
