import pathlib
import shutil
import subprocess as sp

import appdirs
import click

from .backup import make_backup
from .inspect import inspect
from .server import status
from .util import CKANINI


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group()
def cli():
    pass


@click.command()
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to reset your DCOR installation?')
@click.pass_context
def reset(ctx):
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

    click.secho('DCOR reset: SUCCESS', fg=u'green', bold=True)
    click.secho('Please delete resources yourself!', fg=u'green', bold=True)


cli.add_command(inspect)
cli.add_command(reset)
cli.add_command(status)
