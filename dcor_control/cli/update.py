import subprocess as sp

import click

from ..update import update_package


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
