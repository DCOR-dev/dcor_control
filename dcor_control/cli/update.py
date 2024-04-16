import subprocess as sp

import click

from ..update import update_package
from ..inspect import reload_supervisord


@click.command()
@click.confirmation_option(
    prompt="Are you sure you want to update your DCOR installation?")
def update():
    """Update all DCOR CKAN extensions using pip/git"""
    sp.check_output("pip install --upgrade pip", shell=True)

    for name in [
        "dcor_shared",
        "ckanext-dc_log_view",
        "ckanext-dc_serve",
        "ckanext-dc_view",
        "ckanext-dcor_depot",
        "ckanext-dcor_schemas",
        "ckanext-dcor_theme",
        "dcor_control",
    ]:
        update_package(name)

    reload_supervisord()
    click.secho('DONE', fg=u'green', bold=True)
