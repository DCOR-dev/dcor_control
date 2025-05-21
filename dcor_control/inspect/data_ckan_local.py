from functools import lru_cache
import os
import pathlib
import subprocess as sp

from dcor_shared import paths


def ask(prompt):
    an = input(prompt + " [y/N]: ")
    return an.lower() == "y"


@lru_cache(maxsize=32)
def get_resource_ids():
    ckan_ini = paths.get_ckan_config_path()
    data = sp.check_output(
        f"ckan -c {ckan_ini} list-all-resources",
        shell=True).decode().split("\n")
    return data


def remove_empty_folders(path):
    """Recursively remove empty folders"""
    path = pathlib.Path(path)
    if not path.is_dir():
        return

    # recurse into sub-folders
    for pp in path.glob("*"):
        remove_empty_folders(pp)

    if len(list(path.glob("*"))) == 0:
        os.rmdir(path)
