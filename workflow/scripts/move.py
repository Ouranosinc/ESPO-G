import xscen as xs
from xscen import CONFIG
if 1==0: #trick vscode
    import snakemake

from workflow.scripts.utils import zip_directory

xs.load_config("config/config_general.yml", "config/config_region.yml", "config/paths.yml")

if __name__ == '__main__':

    for name, path in snakemake.input.items():
        zip_directory(path, getattr(snakemake.output,name))


