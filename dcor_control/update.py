import os
import pathlib
import subprocess as sp
import sys

import click


def get_package_version(name):
    info = sp.check_output("pip show {}".format(name), shell=True)
    version = info.decode("utf-8").split("\n")[1].split()[1]
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


def update_package(name):
    old_ver = get_package_version(name)
    for path_item in sys.path:
        if name in path_item:
            # This means that the package is probably installed
            # in editable mode.
            is_git = (pathlib.Path(path_item) / ".git").exists()
            if is_git:
                click.secho("Attempting to update git repository "
                            + "at '{}'.".format(path_item), bold=True)
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
        click.secho("Updating package '{}' using pip...".format(name),
                    bold=True)
        sp.check_output("pip install --upgrade {}".format(name),
                        shell=True)
    new_ver = get_package_version(name)
    if old_ver != new_ver:
        print("...updated {} from {} to {}.".format(name, old_ver, new_ver))


@click.command()
@click.confirmation_option(
    prompt="Are you sure you want to update your DCOR installation?")
def update():
    """Update all DCOR CKAN extensions using pip/git"""
    for name in [
        "ckanext-dc_log_view",
        "ckanext-dc_serve",
        "ckanext-dc_view",
        "ckanext-dcor_depot",
        "ckanext-dcor_schemas",
        "ckanext-dcor_theme",
        "dcor_shared",
        "dcor_control",
    ]:
        update_package(name)

    click.secho("Reloading CKAN...", bold=True)
    sp.check_output("supervisorctl reload", shell=True)
