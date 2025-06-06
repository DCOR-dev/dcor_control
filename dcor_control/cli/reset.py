import pathlib
import shutil
import subprocess as sp

import appdirs
import click
from dcor_shared import paths

from .common import reload_supervisord

from ..backup import db_backup


@click.command()
@click.option('--cache', is_flag=True, help='Delete webassets')
@click.option('--database', is_flag=True, help='Reset the DCOR database')
@click.option('--datasets', is_flag=True, help='Purge all datasets')
@click.option('--zombie-users', is_flag=True,
              help='Purge users inactive for 3 months without datasets')
@click.option('--search-index', is_flag=True, help='Reset Solr search index')
@click.option('--control', is_flag=True, help='Delete dcor_control cache')
@click.option('--keep-user', multiple=True,
              help='Username to protect from purging, '
                   'may be used multiple times')
@click.confirmation_option(prompt="Are you certain?")
def reset(cache=False, database=False, datasets=False, zombie_users=False,
          search_index=False, control=False, keep_user=None):
    """Perform (partial) database/cache resets"""
    ckan_ini = paths.get_ckan_config_path()
    if database and datasets:
        raise ValueError("Please select only one of `database` or `dataset`!")

    # if applicable, run backup
    if database or datasets or zombie_users:
        bpath = db_backup()
        click.secho(f"Created backup at {bpath}", bold=True)

    # run CKAN commands
    ckan_cmds = []
    if cache:
        ckan_cmds.append("asset clean")
    if database:
        ckan_cmds.append("db clean --yes")
        ckan_cmds.append("db init")
    elif datasets:
        ckan_cmds.append("dataset list | awk 'FNR>2 {system("
                         + f'"ckan -c {ckan_ini} dataset purge "' + "$1)}'")
    if zombie_users:  # must come after dataset purge
        if keep_user:
            keep_grep = " ".join([f"| grep -v ^{u}$" for u in keep_user])
        else:
            keep_grep = ""
        ckan_cmds.append(
            f"list-zombie-users {keep_grep} | xargs --no-run-if-empty -n1 "
            + f"ckan -c {ckan_ini} user remove")
    if search_index:
        ckan_cmds.append("search-index clear")
    ckan_base = f"ckan -c {ckan_ini} "
    for cmd in ckan_cmds:
        click.secho("Running ckan {}...".format(cmd), bold=True)
        sp.check_output(ckan_base + cmd, shell=True)

    # reset dcor_control cached data
    if control:
        click.secho("Deleting dcor_control config...", bold=True)
        cpath = pathlib.Path(appdirs.user_config_dir("dcor_control"))
        shutil.rmtree(cpath, ignore_errors=True)

    # restart
    reload_supervisord()

    if database or datasets:
        msg = " - Please delete resources yourself!"
    else:
        msg = ""
    click.secho('DONE' + msg, fg=u'green', bold=True)
