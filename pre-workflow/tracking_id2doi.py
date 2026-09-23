"""
Get DOI from tracking_in.
Run on login node to access the internet.
pyact espov2
source <ENVDIR>/cmipcite/bin/activate
python tracking_id2doi.py
"""

import json

import xscen as xs
from cmipcite.citations import get_doi_and_version
from xscen import CONFIG


xs.load_config(
    "../config/config_ESPO.yml",
    "../config/paths_ESPO.yml",
    reset=True,
)

if __name__ == "__main__":
    with open(
        f"{CONFIG['paths']['final']}/inputchecks/input_tracking_ids.json",
    ) as file:
        tracking_ids_dict = json.load(file)

    zenodo_dict = {}
    zenodo_dict["related_identifiers"] = [{"CRCM5-SN": "no dataset DOI."}]
    all_dois = []
    missing_1 = []
    missing_2 = []
    got_all = []
    for pool_id, tracking_ids in tracking_ids_dict.items():
        if "ScenarioMIP" in pool_id:  # no citation CORDEX
            print(pool_id)
            dois = []

            for t in tracking_ids:
                if t is not None:
                    # print(t)
                    try:
                        dois.append(
                            get_doi_and_version(
                                t,
                                doi_granularity="experiment",
                                # sometimes doi not connected to latest
                                multi_dataset_handling="first",
                                # FIXME: update when new arg in cmip PR merge
                            )[0]
                        )
                    except ValueError:
                        print(f"cmipcite failed on {t}")
            dois = list(set(dois))
            if len(dois) == 0:
                missing_2.append(pool_id)
            elif len(dois) == 1:  # should have a ssp and a historical DOI
                missing_1.append(pool_id)
            else:
                got_all.append(pool_id)

            all_dois.extend(dois)
    zenodo_dict["related_identifiers"].append({'missing 1': list(set(missing_1))})
    zenodo_dict["related_identifiers"].append({'missing 2': list(set(missing_2))})
    zenodo_dict["related_identifiers"].append({'got all': list(set(got_all))})
    # remove duplicate historical
    all_dois = list(set(all_dois))
    for doi in all_dois:
        zenodo_dict["related_identifiers"].append(
            {
                "scheme": "doi",
                "identifier": doi,
                "relation": "isDerivedFrom",
                "resource_type": "dataset",
            },
        )
    with open(
        f"{CONFIG['paths']['final']}/inputchecks/input_related_identifiers.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(zenodo_dict, file, indent=4)
