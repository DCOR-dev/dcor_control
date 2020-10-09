import click

from .backup import encrypted_database_backup
from .inspect import inspect
from .reset import reset
from .scan import scan
from .server import status
from .update import update


@click.group()
def cli():
    pass


cli.add_command(encrypted_database_backup)
cli.add_command(inspect)
cli.add_command(reset)
cli.add_command(scan)
cli.add_command(status)
cli.add_command(update)
