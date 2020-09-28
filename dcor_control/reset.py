import pathlib
import shutil
import subprocess as sp

import appdirs
import click

from .backup import db_backup
from .util import CKANINI


@click.command()
@click.option('--cache', is_flag=True, help='Delete webassets')
@click.option('--database', is_flag=True, help='Reset the DCOR database')
@click.option('--datasets', is_flag=True, help='Reset search index')
@click.option('--search_index', is_flag=True, help='Reset Solr search index')
@click.option('--control', is_flag=True, help='Delete dcor_control cache')
@click.confirmation_option(prompt="Are you certain?")
def reset(cache=False, database=False, datasets=False, search_index=False,
          control=False):
    """Perform (partial) database/cache resets"""
    if database and datasets:
        raise ValueError("Please select only one of `database` or `dataset`!")
    ckan_cmds = []
    if cache:
        ckan_cmds.append("asset clean")
    if database or datasets:
        bpath = db_backup()
        click.secho("Created backup at {}".format(bpath), bold=True)
    if database:
        ckan_cmds.append("db clean --yes")
        ckan_cmds.append("db init")
    elif datasets:
        ckan_cmds.append("dataset list | awk 'FNR>2 {system("
                         + '"ckan -c {} dataset purge "'.format(CKANINI)
                         + "$1)}'")
    if search_index:
        ckan_cmds.append("search-index clear")

    # run CKAN commands
    ckan_base = "ckan -c {} ".format(CKANINI)
    for cmd in ckan_cmds:
        click.secho("Running ckan {}...".format(cmd), bold=True)
        sp.check_output(ckan_base + cmd, shell=True)

    if control:
        # reset user data
        click.secho("Deleting dcor_control config...", bold=True)
        cpath = pathlib.Path(appdirs.user_config_dir("dcor_control"))
        shutil.rmtree(cpath, ignore_errors=True)

    # restart
    click.secho("Reloading CKAN...", bold=True)
    sp.check_output("sudo supervisorctl reload", shell=True)

    if database or datasets:
        msg = " - Please delete resources yourself!"
    else:
        msg = ""
    click.secho('DONE' + msg, fg=u'green', bold=True)
