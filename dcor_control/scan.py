from collections import OrderedDict
from functools import lru_cache
import os
import pathlib
import subprocess as sp
import time

import click

from dcor_shared import get_resource_path, DC_MIME_TYPES

from ckanext.dc_serve.jobs import generate_condensed_dataset_job
from ckanext.dc_view.jobs import create_preview_job

from . import util


#: list of valid ancillary files and the functions that generate them
ANCILLARY_FILES = OrderedDict()
ANCILLARY_FILES["condensed.rtdc"] = generate_condensed_dataset_job
ANCILLARY_FILES["preview.jpg"] = create_preview_job

#: CKAN resources path
CKAN_RESOURCES = util.get_storage_path() / "resources"
#: DCOR users depot path
USER_DEPOT = util.get_users_depot_path()


def ask(prompt):
    an = input(prompt + " [y/N]: ")
    return an.lower() == "y"


@lru_cache(maxsize=32)
def get_resource_ids():
    data = sp.check_output(
        "ckan -c {} list-all-resources".format(util.CKANINI),
        shell=True).decode().split("\n")
    return data


def generate_ancillary_files(resource_id, autocorrect=False):
    rp = get_resource_path(resource_id)
    rt = rp.resolve()
    if rt.suffix in DC_MIME_TYPES.values():  # check mime type
        for ap in ANCILLARY_FILES:
            ppap = rp.with_name(rp.name + "_" + ap)
            if not ppap.exists():
                if autocorrect:
                    print("Generating {}".format(ppap))
                    create = True
                else:
                    create = ask(
                        "Ancillary '{}' does not exist, create?".format(ppap))
                if create:
                    res = {"id": resource_id,
                           "mimetype": "DC"}
                    ANCILLARY_FILES[ap](res)


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
    rp = get_resource_path(resource_id)
    todel = []

    # Resource file
    if rp.exists():
        todel.append(rp)

    # Check for ancillary files
    for key in ANCILLARY_FILES:
        ap = rp.with_name(rp.name + "_" + key)
        if ap.exists():
            todel.append(ap)

    # Check for symlinks
    if rp.is_symlink():
        target = rp.resolve()
        # Only delete symlinked files if they are in the USER_DEPOT
        # (we don't delete figshare or internal data)
        if str(target).startswith(str(USER_DEPOT)):
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
            if str(pp).startswith(str(CKAN_RESOURCES)):
                # /data/ckan-HOSTNAME/resources/00e/a65/e6-cc35-...
                remove_empty_folders(pp.parent.parent)
            elif str(pp).startswith(str(USER_DEPOT)):
                # /data/depots/users-HOSTNAME/USER-ORG/f5/ba/pkg_rid_file.rtdc
                remove_empty_folders(pp.parent.parent.parent)


@click.command()
@click.option('--missing', is_flag=True, help='Find missing ancillary files')
@click.option('--orphans', is_flag=True, help='Find orphaned files')
@click.option('--assume-yes', is_flag=True)
def scan(missing=False, orphans=False, assume_yes=False):
    """Scan CKAN resources

    Parameters
    ----------
    orphans: bool

        - checks whether resources in `CKAN_RESOURCES` exist in CKAN
        - checks whether ancillary files ("resource-id_*") in
          `CKAN_RESOURCES` are orphaned
        - checks whether there are datasets in `USER_DEPOT` that
          do not exist in CKAN
    """
    resources_path = pathlib.Path(CKAN_RESOURCES)
    userdepot_path = pathlib.Path(USER_DEPOT)
    time_stop = time.time()
    click.secho("Collecting resource ids...", bold=True)
    resource_ids = get_resource_ids()
    # processed files are used to avoid asking the user multiple times
    orphans_processed = []
    missing_processed = []

    click.secho("Scanning resource tree...", bold=True)
    # Scan CKAN resources
    for pp in resources_path.rglob("*/*/*"):
        if (pp.is_dir()  # directories
            or not pp.exists()  # removed files
                or pp.stat().st_ctime > time_stop):  # newly created resources
            continue
        else:
            res_id = pp.parent.parent.name + pp.parent.name + pp.name[:30]
            exists = res_id in resource_ids
            if orphans and not exists and res_id not in orphans_processed:
                remove_resource_data(res_id, autocorrect=assume_yes)
                orphans_processed.append(res_id)
            if missing and exists and res_id not in missing_processed:
                generate_ancillary_files(res_id, autocorrect=assume_yes)
                missing_processed.append(res_id)

    # Scan user depot for orphans
    if orphans:
        click.secho("Scanning user depot tree...", bold=True)
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
