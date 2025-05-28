import shutil
import subprocess as sp

import click


# Check whether sudo is available, otherwise assume root permissions
SUDO = "sudo " if shutil.which("sudo") else ""


def is_supervisord_running():
    """Simple check for whether supervisord is running"""
    try:
        sp.check_output(SUDO + "supervisorctl status", shell=True)
    except sp.CalledProcessError:
        return False
    else:
        return True


def reload_supervisord():
    if is_supervisord_running():
        click.secho("Reloading CKAN...", bold=True)
        sp.check_output(SUDO + "supervisorctl reload", shell=True)
    else:
        click.secho("Not reloading CKAN (supervisord not running)...",
                    bold=True, fg="red")
