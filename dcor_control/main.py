import pathlib
import shutil
import subprocess as sp

import appdirs
import click

from .backup import make_backup
from .inspect import inspect
from .scan import scan
from .server import status
from .update import update
from .util import CKANINI


@click.group()
def cli():
    pass


@click.command()
@click.confirmation_option(
    prompt="Are you sure you want to reset your DCOR installation?")
def reset():
    """Reset DCOR database, webassets, and solr search index

    Before resetting the database, a dump is created in /backup/
    """
    bpath = make_backup()
    click.secho("Created backup at {}".format(bpath), bold=True)
    # reset CKAN
    ckan_cmd = "ckan -c {} ".format(CKANINI)
    for cmd in [
        "asset clean",
        "db clean --yes",
        "db init",
        "search-index clear"
    ]:
        click.secho("Running ckan {}...".format(cmd), bold=True)
        sp.call(ckan_cmd + cmd, shell=True, stdout=sp.DEVNULL)

    # reset user data
    click.secho("Deleting user config...", bold=True)
    cpath = pathlib.Path(appdirs.user_config_dir("dcor_control"))
    shutil.rmtree(cpath, ignore_errors=True)

    # restart
    click.secho("Reloading CKAN...", bold=True)
    sp.call("sudo supervisorctl reload", shell=True, stdout=sp.DEVNULL)

    click.secho('DCOR reset: SUCCESS - Please delete resources yourself!',
                fg=u'green', bold=True)


cli.add_command(inspect)
cli.add_command(reset)
cli.add_command(scan)
cli.add_command(status)
cli.add_command(update)
