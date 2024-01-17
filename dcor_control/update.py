import functools
import os
import pathlib
import subprocess as sp
import sys

import click
# replace this import when dropping support for Python 3.8
# from importlib import resources as importlib_resources
import importlib_resources


def get_max_compatible_version(name, ckan_version=None):
    """Largest version number of a Python package compatible with current CKAN

    This is done according to the following schema
    - parse ``resources/compatible_versions.txt``
    - compare the latest CKAN version in that file with the current CKAN
    - if current CKAN matches or is newer, return None
    - if current version is lower (compatibility mode), return the
      latest package version listed in `compatible_versions.txt`

    Parameters
    ----------
    name: str
        Name of the package to install, e.g. "ckanext.dc_log_view"
    ckan_version: str
        CKAN version to consider (used in testing). If not provided,
        the currently installed CKAN version is used.
    """
    # parse ``resources/compatible_versions.txt``
    compatible_versions = parse_compatible_versions()

    # compare the latest CKAN version in that file with the current CKAN
    vdict0 = compatible_versions[0]
    # If CKAN is not installed, `get_package_version` will return `None`.
    ckan_cur = ckan_version or get_package_version("ckan") or vdict0["ckan"]
    if version_greater_equal(ckan_cur, vdict0["ckan"]):
        # if current CKAN matches or is newer, return None
        max_version = None
    else:
        # if current version is lower (compatibility mode), return the
        # latest package version listed in `compatible_versions.txt`
        for vdict in compatible_versions:
            if vdict["ckan"] == ckan_cur:
                max_version = vdict[name]
                break
        else:
            raise IndexError(f"Could not find current CKAN version {ckan_cur} "
                             f"in 'compatible_versions.txt'")
    return max_version


def get_package_version(name):
    """Return version string of an installed Python package, None otherwise"""
    try:
        info = sp.check_output(f"pip show {name}", shell=True).decode("utf-8")
    except sp.CalledProcessError:
        info = "error"

    if info.count("Version:"):
        version = info.split("\n")[1].split()[1]
    else:
        version = None
    return version


def package_is_editable(name):
    """Is the package an editable install?

    This only works if the package name is in sys.path somehow.
    It is not a universal solution, but works for DCOR!
    """
    for path_item in sys.path:
        if name in path_item:
            return True
    return False


@functools.lru_cache()
def parse_compatible_versions():
    """Return a list of dicts containing compatible versions

    Data are taken from ``resources/compatible_versions.txt``

    The returned list preserves the order in the file, entries
    at the top are at the beginning of the list.
    """
    data = importlib_resources.files("dcor_control.resources").joinpath(
        "compatible_versions.txt").read_text()
    lines = data.split("\n")
    header = lines.pop(0).strip().split()
    compatible_versions = []
    for line in lines:
        version_dict = {}
        versions = line.strip().split()
        if versions:  # ignore empty lines
            for key, val in zip(header, versions):
                version_dict[key] = val
            compatible_versions.append(version_dict)
    return compatible_versions


def update_package(name):
    """Update a DCOR-related Python package"""
    old_ver = get_package_version(name)
    for path_item in sys.path:
        if name in path_item:
            # This means that the package is probably installed
            # in editable mode.
            is_git = (pathlib.Path(path_item) / ".git").exists()
            if is_git:
                click.secho(f"Attempting to update git repository "
                            f"at '{path_item}'.", bold=True)
                wd = os.getcwd()
                os.chdir(path_item)
                try:
                    sp.check_output("git pull", shell=True)
                except sp.CalledProcessError:
                    click.secho("...failed!", bold=True)
                else:
                    sp.check_output("pip install -e .", shell=True)
                finally:
                    os.chdir(wd)
                break
    else:
        click.secho(f"Updating package '{name}' using pip...", bold=True)
        # Perform a compatible version check
        req_version = get_max_compatible_version(name)
        if req_version is not None:
            pin = f"=={req_version}"
        else:
            pin = ""
        sp.check_output(f"pip install --upgrade {name}{pin}", shell=True)
    new_ver = get_package_version(name)
    if old_ver != new_ver:
        print(f"...updated {name} from {old_ver} to {new_ver}.")


def version_greater(va: str, vb: str):
    """Return True when `va` is greater than `vb`, False otherwise"""
    va = va.strip()
    vb = vb.strip()

    val = va.split(".")
    vbl = vb.split(".")
    max_len = max(len(val), len(vbl))

    for ii in range(max_len):
        try:
            ai = val[ii]
        except IndexError:
            ai = "0"
        try:
            bi = vbl[ii]
        except IndexError:
            bi = "0"
        if ai != bi:
            if ai.isdigit() and bi.isdigit():
                # We have integers
                return int(ai) > int(bi)
            else:
                # We have strings, compare them alphabetically
                return version_greater(
                    va=".".join([f"{ord(char)}" for char in ai]),
                    vb=".".join([f"{ord(char)}" for char in bi])
                )
    # versions match
    return False


def version_greater_equal(va: str, vb: str):
    """Return True when `va` is greater/equal to `vb`, False otherwise"""
    va = va.strip()
    vb = vb.strip()
    return va == vb or version_greater(va, vb)
