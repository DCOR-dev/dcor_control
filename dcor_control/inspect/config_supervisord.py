import subprocess as sp

import click
from dcor_shared.paths import get_supervisord_worker_config_path

from .common import ask


def check_supervisord(autocorrect):
    """Check whether the separate dcor worker files exist"""
    svd_path = get_supervisord_worker_config_path()
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


def is_supervisord_running():
    """Simple check for whether supervisord is running"""
    try:
        sp.check_output("sudo supervisorctl status", shell=True)
    except sp.CalledProcessError:
        return False
    else:
        return True


def reload_supervisord():
    if is_supervisord_running():
        click.secho("Reloading CKAN...", bold=True)
        sp.check_output("sudo supervisorctl reload", shell=True)
    else:
        click.secho("Not reloading CKAN (supervisord not running)...",
                    bold=True, fg="red")
