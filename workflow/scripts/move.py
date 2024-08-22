import xscen as xs
from xscen import CONFIG

xs.load_config("config/config.yml","config/paths.yml")

if __name__ == '__main__':

    def zip_directory(root, zipfile, **zip_args):
        root = Path(root)

        def _add_to_zip(zf, path, root):
            zf.write(path, path.relative_to(root))
            if path.is_dir():
                for subpath in path.iterdir():
                    _add_to_zip(zf, subpath, root)

        with ZipFile(zipfile, "w", **zip_args) as zf:
            for file in root.iterdir():
                _add_to_zip(zf, file, root)

    zip_directory(snakemake.input.final, snakemake.output.final)

    zip_directory(snakemake.input.regchunked, snakemake.output.regchunked)



