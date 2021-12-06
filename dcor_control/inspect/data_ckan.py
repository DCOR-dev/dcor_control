from functools import lru_cache
import os
import pathlib
import subprocess as sp
import time

import click

from dcor_shared import get_resource_path

from . import paths


def ask(prompt):
    an = input(prompt + " [y/N]: ")
    return an.lower() == "y"


@lru_cache(maxsize=32)
def get_resource_ids():
    ckan_ini = paths.get_ckan_config_path()
    data = sp.check_output(
        f"ckan -c {ckan_ini} list-all-resources",
        shell=True).decode().split("\n")
    return data


def remove_empty_folders(path):
    """Recursively remove empty folders"""
    path = pathlib.Path(path)
    if not path.is_dir():
        return

    # recurse into subfolders
    for pp in path.glob("*"):
        remove_empty_folders(pp)

    if len(list(path.glob("*"))) == 0:
        os.rmdir(path)


def remove_resource_data(resource_id, autocorrect=False):
    """Remove all data related to a resource

    This includes ancillary files as well as data in the user depot.
    If `autocorrect` is False, the user is prompted before deletion.
    """
    resources_path = paths.get_ckan_storage_path() / "resources"
    userdepot_path = paths.get_dcor_users_depot_path()

    rp = get_resource_path(resource_id)
    todel = []

    # Resource file
    if rp.exists() or rp.is_symlink():  # sometimes symlinks don't "exist" :)
        todel.append(rp)

    # Check for ancillary files
    todel += sorted(rp.parent.glob(rp.name + "_*"))

    # Check for symlinks and remove the corresponding files in the user depot
    if rp.is_symlink():
        try:
            target = rp.resolve()
        except RuntimeError:
            # Symlink loop
            target = pathlib.Path(os.path.realpath(rp))
        # Only delete symlinked files if they are in the user_depot
        # (we don't delete figshare or internal data)
        if target.exists() and str(target).startswith(str(userdepot_path)):
            todel.append(target)

    if autocorrect:
        for pp in todel:
            print("Deleting {}".format(pp))
        delok = True
    else:
        delok = ask(
            "These files are not related to an existing resource: "
            + "".join(["\n - {}".format(pp) for pp in todel])
            + "\nDelete these orphaned files?"
        )
    if delok:
        for pp in todel:
            pp.unlink()
            # Also remove empty dirs
            if str(pp).startswith(str(resources_path)):
                # /data/ckan-HOSTNAME/resources/00e/a65/e6-cc35-...
                remove_empty_folders(pp.parent.parent)
            elif str(pp).startswith(str(userdepot_path)):
                # /data/depots/users-HOSTNAME/USER-ORG/f5/ba/pkg_rid_file.rtdc
                remove_empty_folders(pp.parent.parent.parent)


def check_orphaned_files(assume_yes=False):
    resources_path = paths.get_ckan_storage_path() / "resources"
    userdepot_path = paths.get_dcor_users_depot_path()
    time_stop = time.time()
    click.secho("Collecting resource ids...", bold=True)
    resource_ids = get_resource_ids()
    orphans_processed = []  # list for keeping track of orphans

    click.secho("Scanning resource tree for orphaned files...", bold=True)
    # Scan CKAN resources
    for pp in resources_path.rglob("*/*/*"):
        if (pp.is_dir()  # directories
            or not pp.exists()  # removed files
                or pp.stat().st_ctime > time_stop):  # newly created resources
            continue
        else:
            res_id = pp.parent.parent.name + pp.parent.name + pp.name[:30]
            # check for orphans
            if res_id not in resource_ids:
                remove_resource_data(res_id, autocorrect=assume_yes)
                orphans_processed.append(res_id)

    # Scan user depot for orphans
    click.secho("Scanning user depot tree for orphaned files...", bold=True)
    for pp in userdepot_path.rglob("*/*/*/*"):
        res_id = pp.name.split("_")[1]
        if res_id not in resource_ids and res_id not in orphans_processed:
            if assume_yes:
                print("Deleting {}".format(pp))
                delok = True
            else:
                delok = ask("Delete orphaned file '{}'?".format(pp))
            if delok:
                pp.unlink()
                remove_empty_folders(pp.parent.parent.parent)
                orphans_processed.append(res_id)
