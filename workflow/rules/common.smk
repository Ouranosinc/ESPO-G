from pathlib import Path

from snakemake.utils import validate

def inter_region():
    file_ref = []
    calandar = ["_default.zarr", "_noleap.zarr", "_360_day.zarr"]
    for region_name in config['custom']['regions'].keys():
        for cal in calandar:
            file_ref.append(Path(config['paths']['refdir'])/f"ref_{region_name}{cal}")
    return file_ref