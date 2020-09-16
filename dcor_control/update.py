import subprocess as sp
import sys

import click


def package_is_editable(name):
    """Is the package an editable install?

    This only works if the package name is in sys.path somehow.
    It is not a universal solution, but works for DCOR!
    """
    for path_item in sys.path:
        if name in path_item:
            return True
    return False


@click.command()
@click.confirmation_option(
    prompt="Are you sure you want to update your DCOR installation?")
def update():
    """Update all DCOR CKAN extensions"""
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
        if not package_is_editable(name):
            click.secho("Updating '{}'...".format(name), bold=True)
            sp.check_output("pip install --upgrade {}".format(name),
                            shell=True)
        else:
            click.secho("Not updating '{}', because it looks".format(name)
                        + "like an editable install.", bold=True)
