"""List the current versions of the DCOR extensions

The output of this script should be written to
dcor_control/resources/compatible_versions.csv.
The idea is to have a trace of compatible DCOR
extensions. This should be done on a regular basis,
but at the least whenever an incompatibility is
introduced.
"""
import pathlib

import ckan
from dcor_control import update


packages = [
    "ckan",
    "ckanext.dc_log_view",
    "ckanext.dc_serve",
    "ckanext.dc_view",
    "ckanext.dcor_depot",
    "ckanext.dcor_schemas",
    "ckanext.dcor_theme",
    "dcor_control",
    "dcor_shared",
]

versions = {}

git_search_path = pathlib.Path(__file__).resolve().parent.parent.parent

for name in packages:
    print(f"Detecting {name}")
    if name == "ckan":
        new_ver = ckan.__version__
    else:
        try:
            new_ver = update.get_package_version_git(name, git_search_path)
        except ValueError:
            print("Could not get package version from git")
            new_ver = update.get_package_version(name)
    versions[name] = new_ver


min_cell_width = 10

keys = sorted(versions.keys())

key_line = ""
ver_line = ""

for kk in keys:
    cell_width = max(min_cell_width, len(kk) + 2)
    key_line += kk.ljust(cell_width)
    ver_line += versions[kk].ljust(cell_width)

print(key_line)
print(ver_line)
