import socket

import click

from ..inspect.config_ckan import get_expected_ckan_options, get_ip
from ..inspect.paths import get_ckan_config_path


@click.command()
def status():
    """Display DCOR status"""
    srv_opts = get_expected_ckan_options()
    click.secho(f"DCOR installation: '{srv_opts['name']}'", bold=True)
    click.echo(f"IP Address: {get_ip()}")
    click.echo(f"Hostname: {socket.gethostname()}")
    click.echo(f"CKAN_INI: {get_ckan_config_path()}")