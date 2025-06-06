import os
import pathlib
import subprocess as sp
import uuid

import click
from dcor_shared.paths import get_ckan_config_path

from .common import reload_supervisord

from ..inspect import config_ckan
from ..util import get_pip_executable_path


@click.command()
@click.confirmation_option(
    prompt="Are you sure you want migrate all DCOR-related Python packages "
           "(CKAN extensions and helpers) to an editable install?")
def develop():
    """Migrate all DCOR CKAN extensions to git-based editable installs"""
    pip = get_pip_executable_path()

    sp.check_output(f"{pip} install --upgrade pip", shell=True)
    sp.check_output(f"{pip} install requests requests_toolbelt", shell=True)

    for name in [
        "dcor_shared",
        "ckanext-dc_log_view",
        "ckanext-dc_serve",
        "ckanext-dc_view",
        "ckanext-dcor_depot",
        "ckanext-dcor_schemas",
        "ckanext-dcor_theme",
        "dcor_control",
    ]:
        migrate_to_editable(name)

    # Redo the CSS branding
    print("Applying DCOR CSS branding")
    ckan_ini = get_ckan_config_path()
    ckan_cmd = f"ckan -c {ckan_ini} dcor-theme-main-css-branding"
    sp.check_output(ckan_cmd, shell=True)
    # set config option
    config_ckan.check_ckan_ini_option(
        key="ckan.theme",
        value="dcor_theme_main/dcor_theme_main",
        autocorrect=True)

    reload_supervisord()
    click.secho('DONE', fg=u'green', bold=True)


def migrate_to_editable(name,
                        base_url="https://github.com/DCOR-dev/"):
    """Migrate all DCOR CKAN extensions to git-based editable installs"""
    # make sure the `/dcor-repos` directory exists
    repo_dir = pathlib.Path("/dcor-repos")
    repo_dir.mkdir(parents=True, exist_ok=True)
    click.secho(f"Migrating {name} to {repo_dir}", bold=True)
    # make sure we can write to it
    test_file = repo_dir / f"write-check-{uuid.uuid4()}"
    test_file.touch()
    test_file.unlink()
    # check whether the repository exists
    pkg_dir = repo_dir / name
    git_dir = pkg_dir / ".git"
    wd = os.getcwd()

    if not git_dir.is_dir():
        # clone the repository
        os.chdir(repo_dir)
        sp.check_output(f"git clone {base_url}{name}", shell=True)
    else:
        # update the repository
        os.chdir(pkg_dir)
        sp.check_output("git pull", shell=True)

    os.chdir(wd)
    # install in editable mode
    pip = get_pip_executable_path()
    sp.check_output(f"{pip} install -e {pkg_dir}", shell=True)
