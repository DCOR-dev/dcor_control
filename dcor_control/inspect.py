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


def check_option(key, value, autocorrect=False):
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
            sp.call(ckan_cmd, shell=True, stdout=sp.DEVNULL)


def check_permission(path, user=None, mode=None, autocorrect=False):
    path = pathlib.Path(path)
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


@click.command()
@click.option('--assume-yes', is_flag=True)
def inspect(assume_yes=False):
    """Inspect this DCOR installation"""
    click.secho("Checking custom server options...", bold=True)
    srv_opts = get_server_options()
    for key in srv_opts["ckan.ini"]:
        check_option(key, srv_opts["ckan.ini"][key], autocorrect=assume_yes)

    click.secho("Checking general server options...", bold=True)
    gen_opts = util.parse_config_options(
        resource_filename("dcor_control.resources", "dcor_options.ini"))
    for key in gen_opts:
        check_option(key, gen_opts[key], autocorrect=assume_yes)

    click.secho("Checking www-data permissions...", bold=True)
    for path in [
        util.get_storage_path(),
        util.get_storage_path() / "resources",
        os.path.join(util.get_config_option("ckan.dcor_depot_path"),
                     util.get_config_option("ckan.dcor_user_depot_name")),
        util.get_config_option("ckan.webassets.path")
    ]:
        check_permission(path=path,
                         user="www-data",
                         mode=0o755,
                         autocorrect=assume_yes)

    click.secho("Checking nginx configuration...", bold=True)
    check_nginx(cmbs="10G")

    click.secho("Reloading CKAN...", bold=True)
    sp.call("sudo supervisorctl reload", shell=True, stdout=sp.DEVNULL)
