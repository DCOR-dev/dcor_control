import pathlib
from pkg_resources import resource_filename
import subprocess as sp

import click
from dcor_shared.paths import get_supervisord_worker_config_path

from .common import ask


def check_supervisord(autocorrect):
    """Check whether the separate dcor worker files exist"""
    path_worker = resource_filename(
        "dcor_control.resources.config",
        "etc_supervisor_conf.d_ckan-worker-dcor.conf")
    template = pathlib.Path(path_worker).read_text()

    svd_path = get_supervisord_worker_config_path()
    for worker in ["long", "normal", "short"]:
        wpath = svd_path.with_name(f"ckan-worker-dcor-{worker}.conf")
        if not wpath.exists():
            if autocorrect:
                wcr = True
                print(f"Creating '{wpath}'.")
            else:
                wcr = ask(f"Supervisord entry 'dcor-{worker}' missing")
            if wcr:
                data = template.replace("{{QUEUE}}", f"dcor-{worker}")
                wpath.write_text(data)


def is_nginx_running():
    """Simple check for whether supervisord is running"""
    try:
        sp.check_output("sudo systemctl status nginx", shell=True)
    except sp.CalledProcessError:
        return False
    else:
        return True


def is_supervisord_running():
    """Simple check for whether supervisord is running"""
    try:
        sp.check_output("sudo supervisorctl status", shell=True)
    except sp.CalledProcessError:
        return False
    else:
        return True


def reload_nginx():
    if is_nginx_running():
        click.secho("Reloading nginx...", bold=True)
        sp.check_output("sudo systemctl reload nginx", shell=True)
    else:
        click.secho("Not reloading nginx (not running)...",
                    bold=True, fg="red")


def reload_supervisord():
    if is_supervisord_running():
        click.secho("Reloading CKAN...", bold=True)
        sp.check_output("sudo supervisorctl reload", shell=True)
    else:
        click.secho("Not reloading CKAN (supervisord not running)...",
                    bold=True, fg="red")
