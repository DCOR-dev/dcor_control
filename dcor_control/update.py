import functools
import importlib
import os
import pathlib
import subprocess as sp

import click
# replace this import when dropping support for Python 3.8
# from importlib import resources as importlib_resources
import importlib_resources

from .util import get_pip_executable_path


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
        pip = get_pip_executable_path()
        info = sp.check_output(f"{pip} show {name}",
                               shell=True).decode("utf-8")
    except sp.CalledProcessError:
        info = "error"

    if info.count("Version:"):
        version = info.split("\n")[1].split()[1]
    else:
        version = None
    return version


def get_package_version_git(name, search_path):
    """Return package version based on git tag"""
    search_dirs = [name, name.replace(".", "-")]
    for sdir in search_dirs:
        path = pathlib.Path(search_path) / sdir
        if path.is_dir():
            # Run git describe
            try:
                info = sp.check_output(f"git -C {path} describe",
                                       shell=True).decode("utf-8")
            except BaseException:
                continue
            else:
                return info.strip()
    else:
        raise ValueError(f"Could not find {name} in {search_path}")


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
    wd = os.getcwd()

    # Check whether the package is located in /testing in a testing VM
    test_toml = pathlib.Path("/testing/pyproject.toml")
    if test_toml.exists():
        is_testing = test_toml.read_text().count(
            f'name = "{name}"')
    else:
        is_testing = False

    # Check whether the package is installed -e via git somewhere
    # This means that the package is probably installed
    # in editable mode. Import the package to identify its
    # location.
    mod_name = (name.replace("-", ".", 1)
                if name.startswith("ckanext-") else name)
    mod = importlib.import_module(mod_name)
    for pp in pathlib.Path(mod.__file__).parents:
        if (pp / ".git").exists():
            is_located_git = str(pp)
            break
    else:
        is_located_git = False

    pip = get_pip_executable_path()
    if is_testing:
        click.secho(f"Reinstalling {name} via {test_toml}", bold=True)
        os.chdir(test_toml.parent)
        try:
            sp.check_output(f"{pip} install -e .", shell=True)
        except sp.CalledProcessError:
            click.secho("...failed!", bold=True)
        finally:
            os.chdir(wd)
    elif is_located_git:
        click.secho(f"Attempting to update git repository "
                    f"at '{is_located_git}'.", bold=True)
        os.chdir(is_located_git)
        try:
            sp.check_output("git pull", shell=True)
        except sp.CalledProcessError:
            click.secho("...failed!", bold=True)
        else:
            sp.check_output(f"{pip} install -e .", shell=True)
        finally:
            os.chdir(wd)
    else:
        # Perform a compatible version check
        req_version = get_max_compatible_version(name)
        if req_version is not None:
            click.secho(f"Installing '{name}=={req_version}' using pip...",
                        bold=True)
            pin = f"=={req_version}"
        else:
            click.secho(f"Updating package '{name}' using pip...", bold=True)
            pin = ""
        sp.check_output(f"{pip} install --upgrade {name}{pin}", shell=True)
    new_ver = get_package_version(name)
    if old_ver != new_ver:
        print(f"...updated {name} from {old_ver} to {new_ver}.")
    return new_ver


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
