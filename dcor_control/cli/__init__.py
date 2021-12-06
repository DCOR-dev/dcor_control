import click

from . import backup
from . import info
from . import inspect
from . import update


@click.group()
def cli():
    pass


cli.add_command(backup.encrypted_database_backup)
cli.add_command(inspect.inspsect)
cli.add_command(info.status)
cli.add_command(update.update)
