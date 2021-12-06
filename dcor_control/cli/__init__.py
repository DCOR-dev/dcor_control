import click

from . import backup
from . import info
from . import inspect
from . import update


@click.group()
def main():
    pass


main.add_command(backup.encrypted_database_backup)
main.add_command(inspect.inspsect)
main.add_command(info.status)
main.add_command(update.update)
