from pkg_resources import resource_filename
import subprocess as sp

import click

from .server import get_server_options
from . import util


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
            an = input("'{}' is '{}' but should be '{}'; edit? [y/N]: ".format(
                key, opt, value))
            if an.lower() == "y":
                change = True
            else:
                change = False
        if change:
            ckan_cmd = "ckan config-tool {} '{}={}'".format(util.CKANINI,
                                                            key,
                                                            value)
            sp.call(ckan_cmd, shell=True, stdout=sp.DEVNULL)


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

    click.secho("Reloading CKAN...", bold=True)
    sp.call("sudo supervisorctl reload", shell=True, stdout=sp.DEVNULL)
