"""Get tracking_id of input files."""

import json
from copy import deepcopy

import xarray as xr
import xscen as xs
from xscen import CONFIG
from collections import defaultdict


if __name__ == "__main__":
    xs.load_config(
        "../config/config_ESPO.yml",
        "../config/paths_ESPO.yml",
        reset=True,
    )
    # search cat
    # seaparate historical and future experiments to get both ids
    args = deepcopy(CONFIG["extraction"]["simulation"]["search_data_catalogs"])
    cat_sim_id = xs.search_data_catalogs(
        **args,
    )

    tracking_ids = {}

    for sim_id, dc_id in cat_sim_id.items():
        print(sim_id)
        tracking_ids[sim_id] = []
        for _, row in dc_id.df.iterrows():
            path = row["path"]
            ds = xr.open_dataset(path, engine="h5netcdf", decode_times=False)
            tracking_id = ds.attrs.get("tracking_id", None)
            tracking_ids[sim_id].append(tracking_id)

    # pool sim_ids of ScenarioMIP (one DOI by model-scenario)
    merged = defaultdict(list)
    for key, values in tracking_ids.items():
        if 'ScenarioMIP' in key:
            new_key = "_".join(key.split("_")[:5])
        else:
            new_key = key
        merged[new_key].extend(values)
    out = dict(merged)

    # remove duplicates
    out = {k: list(set(v)) for k, v in out.items()}

    with open(
        f"{CONFIG['paths']['final']}/inputchecks/input_tracking_ids.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(out, file, indent=4)
