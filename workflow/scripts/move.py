import xscen as xs
from xscen import CONFIG

from workflow.scripts.utils import zip_directory

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    for name, path in snakemake.input.items():
        zip_directory(path, getattr(snakemake.output,name))


