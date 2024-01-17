import os
import pathlib
import subprocess as sp
import uuid

import click

from ..inspect import reload_supervisord


@click.command()
@click.confirmation_option(
    prompt="Are you sure you want migrate all DCOR-related Python packages "
           "(CKAN extensions and helpers) to an editable install?")
def develop():
    """Migrate all DCOR CKAN extensions to git-based editable installs"""
    for name in [
        "ckanext-dc_log_view",
        "ckanext-dc_serve",
        "ckanext-dc_view",
        "ckanext-dcor_depot",
        "ckanext-dcor_schemas",
        "ckanext-dcor_theme",
        "dcor_shared",
        "dcor_control",
    ]:
        migrate_to_editable(name)

    reload_supervisord()
    click.secho('DONE', fg=u'green', bold=True)


def migrate_to_editable(name,
                        base_url="https://github.com/DCOR-dev/"):
    """Migrate all DCOR CKAN extensions to git-based editable installs"""
    # make sure the `/dcor-repos` directory exists
    repo_dir = pathlib.Path("/dcor-repos")
    repo_dir.mkdir(parents=True, exist_ok=True)
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
    sp.check_output(f"pip install -e {pkg_dir}", shell=True)
