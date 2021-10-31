import os
import grp
import pathlib
from pkg_resources import resource_filename
import pwd
import stat
import subprocess as sp

import click

from .server import get_server_options
from . import util


def ask(prompt):
    an = input(prompt + "; fix? [y/N]: ")
    return an.lower() == "y"


def check_nginx(cmbs, autocorrect=False):
    with open("/etc/nginx/sites-enabled/ckan") as fd:
        lines = fd.readlines()
    for ii, line in enumerate(lines):
        if not line.strip() or line.startswith("#"):
            continue
        elif line.strip().startswith("client_max_body_size"):
            cur = line.strip().split()[1].strip(";")
            if cur != cmbs:
                if autocorrect:
                    print("Setting client_max_body_size to {}".format(cmbs))
                    correct = True
                else:
                    correct = ask("'client_max_body_size' should be "
                                  + "'{}', but is '{}'".format(cmbs, cur))
                if correct:
                    lines[ii] = line.replace(cur, cmbs)
                    with open("/etc/nginx/sites-enabled/ckan", "w") as fd:
                        fd.writelines(lines)
            break
    else:
        raise ValueError("'client_max_body_size' not set!")


def check_permission(path, user=None, mode=None, recursive=False,
                     autocorrect=False):
    path = pathlib.Path(path)
    if recursive:
        for pp in path.rglob("*"):
            if pp.is_dir():
                check_permission(path=pp,
                                 user=user,
                                 mode=mode,
                                 recursive=False,
                                 autocorrect=autocorrect)
    if user is not None:
        uid = pwd.getpwnam(user).pw_uid
        gid = grp.getgrnam(user).gr_gid
    else:
        uid = None
        gid = None
    # Check if exists
    if not path.exists():
        if autocorrect:
            print("Creating '{}'".format(path))
            create = True
        else:
            create = ask("'{}' does not exist".format(path))
        if create:
            path.mkdir(parents=True)
            os.chmod(path, mode)
            if user is not None:
                os.chown(path, uid, gid)
    # Check mode
    pmode = stat.S_IMODE(path.stat().st_mode)
    if pmode != mode:
        if autocorrect:
            print("Changing mode of '{}' to '{}'".format(path, oct(mode)))
            change = True
        else:
            change = ask("Mode of '{}' is '{}', but ".format(path, oct(pmode))
                         + "should be '{}'".format(oct(mode)))
        if change:
            os.chmod(path, mode)
    # Check owner
    if user is not None:
        puid = path.stat().st_uid
        try:
            puidset = pwd.getpwuid(puid)
        except KeyError:
            pnam = "unknown"
        else:
            pnam = puidset.pw_name
        if puid != uid:
            if autocorrect:
                print("Changing owner of '{}' to '{}'".format(path, user))
                chowner = True
            else:
                chowner = ask("Owner of '{}' is ".format(path)
                              + "'{}', but should be '{}'".format(pnam, user))
            if chowner:
                os.chown(path, uid, gid)


def check_server_option(key, value, autocorrect=False):
    """Check one server option"""
    try:
        opt = util.get_config_option(key)
    except util.ConfigOptionNotFoundError:
        opt = "NOT SET"
    if opt != value:
        if autocorrect:
            print("Setting '{}={}' (was '{}').".format(key, value, opt))
            change = True
        else:
            change = ask("'{}' is '{}' but should be '{}'".format(
                         key, opt, value))
        if change:
            ckan_cmd = "ckan config-tool {} '{}={}'".format(util.CKANINI,
                                                            key,
                                                            value)
            sp.check_output(ckan_cmd, shell=True)


def check_server_options(autocorrect=False):
    """Check custom ckan.ini server options

    This includes the contributions from
    - general options from resources/dcor_options.ini
    - as well as custom options in resources/server_options.json

    Custom options override general options.
    """
    custom_opts = get_server_options()["ckan.ini"]
    general_opts = util.parse_config_options(
        resource_filename("dcor_control.resources", "dcor_options.ini"))

    general_opts.update(custom_opts)

    for key in general_opts:
        check_server_option(key, general_opts[key], autocorrect=autocorrect)


def check_supervisord(autocorrect):
    """Check whether the separate dcor worker files exist"""
    svd_path = pathlib.Path("/etc/supervisor/conf.d/ckan-worker.conf")
    for worker in ["long", "normal", "short"]:
        wpath = svd_path.with_name("ckan-worker-dcor-{}.conf".format(worker))
        if not wpath.exists():
            if autocorrect:
                wcr = True
                print("Creating '{}'.".format(wpath))
            else:
                wcr = ask("Supervisord entry 'dcor-{}' missing".format(worker))
            if wcr:
                data = svd_path.read_text()
                data = data.replace(
                    "[program:ckan-worker]",
                    "[program:ckan-ckan-worker-dcor-{}]".format(worker))
                data = data.replace(
                    "/ckan.ini jobs worker",
                    "/ckan.ini jobs worker dcor-{}".format(worker))
                wpath.write_text(data)


def check_theme_i18n_hack(autocorrect):
    """Generate the en_US locale and only *after* that set it in ckan.ini

    This will run the command

    .. code::

       ckan -c /etc/ckan/default/ckan.ini dcor-i18n-hack
    """
    try:
        opt = util.get_config_option("ckan.locale_default")
    except util.ConfigOptionNotFoundError:
        opt = "NOT SET"
    if opt != "en_US":
        if autocorrect:
            print("Applying DCOR theme i18n hack")
            hack = True
        else:
            hack = ask("DCOR theme i18n is not setup")
        if hack:
            # apply hack
            ckan_cmd = "ckan -c {} dcor-i18n-hack".format(util.CKANINI)
            sp.check_output(ckan_cmd, shell=True)
            # set config option
            ckan_cmd2 = "ckan config-tool {} '{}={}'".format(
                util.CKANINI, "ckan.locale_default", "en_US")
            sp.check_output(ckan_cmd2, shell=True)


def check_uwsgi(harakiri, autocorrect=False):
    """Set harakiri timeout of uwsgi (important for data upload)

    Parameters
    ----------
    harakiri: int
        uwsgi timeout in minutes
    """
    uwsgi_ini = "/etc/ckan/default/ckan-uwsgi.ini"
    with open(uwsgi_ini) as fd:
        lines = fd.readlines()
    for ii, line in enumerate(lines):
        if line.startswith("harakiri"):
            value = int(line.split("=")[1])
            if value != harakiri:
                if autocorrect:
                    change = True
                    print("Setting UWSGI harakiri to {} min".format(harakiri))
                else:
                    change = ask(
                        "UWSGI timeout should be '{}' min".format(harakiri)
                        + ", but is '{}' min".format(value))
                if change:
                    lines[ii] = line.replace(str(value), str(harakiri))
                    with open(uwsgi_ini, "w") as fd:
                        fd.writelines(lines)


@click.command()
@click.option('--assume-yes', is_flag=True)
def inspect(assume_yes=False):
    """Inspect this DCOR installation"""
    click.secho("Checking CKAN options...", bold=True)
    check_server_options(autocorrect=assume_yes)

    click.secho("Checking www-data permissions...", bold=True)
    for path in [
        util.get_storage_path(),
        util.get_storage_path() / "resources",
        os.path.join(
            util.get_config_option("ckanext.dcor_depot.depots_path"),
            util.get_config_option("ckanext.dcor_depot.users_depot_name")),
        util.get_config_option("ckan.webassets.path")
    ]:
        check_permission(path=path,
                         user="www-data",
                         mode=0o755,
                         autocorrect=assume_yes)
    # Make sure that www-data can upload things into storage
    check_permission(path=util.get_storage_path() / "storage",
                     user="www-data",
                     mode=0o755,
                     autocorrect=assume_yes,
                     recursive=True)

    click.secho("Checking i18n hack...", bold=True)
    check_theme_i18n_hack(autocorrect=assume_yes)

    click.secho("Checking ckan workers...", bold=True)
    check_supervisord(autocorrect=assume_yes)

    click.secho("Checking nginx configuration...", bold=True)
    check_nginx(cmbs="100G", autocorrect=assume_yes)

    click.secho("Checking uwsgi configuration...", bold=True)
    check_uwsgi(harakiri=7200, autocorrect=assume_yes)

    click.secho("Reloading CKAN...", bold=True)
    sp.check_output("supervisorctl reload", shell=True)

    click.secho("Reloading nginx...", bold=True)
    sp.check_output("systemctl reload nginx", shell=True)
