from datetime import datetime, timedelta
from functools import lru_cache
import re
import subprocess as sp

import click

from dcor_shared import get_ckan_config_option, paths, s3

from .data_ckan_local import ask


ARTIFACT_NAMES = ["condensed", "preview", "resource"]


def check_orphaned_s3_artifacts(assume_yes=False, older_than_days=7,
                                purge_orphan_buckets=True):
    """Check all DCOR buckets for orphaned artifacts

    Parameters
    ----------
    assume_yes: bool
        Set to True for non-interactive mode
    older_than_days: int
        Buckets must have this minimum age to be considered for deletion
    purge_orphan_buckets: bool
        Whether to delete buckets that are not related to any circle
    """
    s3_client, _, s3_resource = s3.get_s3()

    # Find buckets that do not belong to an actual circle and delete them
    # list of actual circles
    circles_ckan = get_circles_ckan()

    # list of circles for which we have buckets
    circles_s3 = get_circles_s3(older_than_days=older_than_days)

    # bucket_definition
    bucket_scheme = get_ckan_config_option("dcor_object_store.bucket_name")

    click.secho("Scanning S3 object store for orphaned objects...",
                bold=True)

    # find "older_than_days" S3 circles that are not defined in CKAN
    for cs3 in circles_s3:
        bucket_name = bucket_scheme.format(organization_id=cs3)
        if cs3 not in circles_ckan and purge_orphan_buckets:
            # Purge buckets that are not representing DCOR circles.
            # This is only done if `purge_orphan_buckets` is set.
            click.secho(f"Found S3 bucket for non-existent circle {cs3}")
            request_bucket_removal(
                bucket_name=bucket_name,
                older_than_days=older_than_days,
                autocorrect=assume_yes)
            continue
        # Iterate through the resources of that circle
        circle_resources = list_group_resources_ckan(cs3)

        invalid_artifacts = []
        for object_name in iter_bucket_objects_s3(
                bucket_name, older_than_days=older_than_days):
            artifact = object_name.split("/")[0]
            if artifact in ARTIFACT_NAMES:
                rid = "".join(object_name.split("/")[1:])
                assert len(rid) == 36, "sanity check"
                if rid not in circle_resources:
                    invalid_artifacts.append(object_name)

        if invalid_artifacts:
            # Ask the user whether we should remove these resources for
            # this circle
            request_removal_from_bucket(
                bucket_name=bucket_name,
                objects=invalid_artifacts,
                autocorrect=assume_yes
                )


@lru_cache(maxsize=32)
def get_circles_ckan():
    """Return list of circle IDs defined in CKAN"""
    ckan_ini = paths.get_ckan_config_path()
    data = sp.check_output(
        f"ckan -c {ckan_ini} list-circles",
        shell=True).decode().split("\n")
    circle_list = [f.split()[0] for f in data if f.strip()]
    return circle_list


@lru_cache(maxsize=32)
def get_circles_s3(older_than_days=0):
    """Return list of circle IDs defined in S3"""
    s3_client, _, _ = s3.get_s3()
    buckets = s3_client.list_buckets().get("Buckets", [])
    # compile regexp for identifying cirlces
    bucket_scheme = get_ckan_config_option("dcor_object_store.bucket_name")
    bucket_regexp = re.compile(bucket_scheme.replace(
        r"{organization_id}",
        r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"))

    circle_list = []
    for bdict in buckets:
        creation_date = bdict["CreationDate"]
        tz = creation_date.tzinfo
        if creation_date > (datetime.now(tz=tz)
                            - timedelta(days=older_than_days)):
            # Ignore circles that are younger `older_than_days`
            continue
        # Find circles that match our regular expression scheme
        r_match = bucket_regexp.match(bdict["Name"])
        if r_match is not None:
            circle_id = r_match.group(1)
            circle_list.append(circle_id)
    return circle_list


def iter_bucket_objects_s3(bucket_name, older_than_days=7):
    """Return iterator over all objects in a Bucket"""
    s3_client, _, s3_resource = s3.get_s3()
    kwargs = {"Bucket": bucket_name,
              "MaxKeys": 100
              }
    while True:
        try:
            resp = s3_client.list_objects_v2(**kwargs)
        except s3_client.exceptions.NoSuchBucket:
            # Bucket has been deleted in the meantime
            break

        for obj in resp.get("Contents", []):
            object_name = obj["Key"]
            creation_date = obj.get("LastModified", obj.get("CreationDate"))
            tz = creation_date.tzinfo
            if creation_date > (datetime.now(tz=tz)
                                - timedelta(days=older_than_days)):
                # Ignore objects that are younger than `older_than_days`
                continue
            yield object_name

        if not resp.get("IsTruncated"):
            break
        else:
            kwargs["ContinuationToken"] = resp.get("NextContinuationToken")


def list_group_resources_ckan(group_name_or_id):
    """Return list of resources for a circle or collection"""
    ckan_ini = paths.get_ckan_config_path()
    try:
        data = sp.check_output(
            f"ckan -c {ckan_ini} list-group-resources {group_name_or_id}",
            shell=True).decode().split("\n")
        resources = [f.strip() for f in data if f.strip()]
    except sp.CalledProcessError:
        resources = []
    return resources


def request_bucket_removal(bucket_name, older_than_days=7, autocorrect=False):
    """Request (user interaction) the removal of an entire bucket"""
    if autocorrect:
        print(f"Deleting bucket {bucket_name}")
        del_ok = True
    else:
        del_ok = ask(f"Completely remove orphan bucket {bucket_name}?")

    if del_ok:
        s3_client, _, _ = s3.get_s3()
        # Delete the objects
        request_removal_from_bucket(
            bucket_name=bucket_name,
            objects=iter_bucket_objects_s3(bucket_name,
                                           older_than_days=older_than_days),
            autocorrect=True
        )
        # Delete the bucket if it is not empty
        if len(list(
                iter_bucket_objects_s3(bucket_name,
                                       older_than_days=older_than_days))) == 0:
            try:
                s3_client.delete_bucket(Bucket=bucket_name)
            except s3_client.exceptions.NoSuchBucket:
                # bucket has been deleted in the meantime
                pass


def request_removal_from_bucket(bucket_name, objects, autocorrect=False):
    """Request (user interaction) and perform removal of a list of objects

    Parameters
    ----------
    bucket_name: str
        The bucket from which to remote the objects
    objects: list of str or iterable of str
        The objects to be removed
    autocorrect: bool
        Whether to remove the objects without asking the user
    """
    if autocorrect:
        for obj in objects:
            print(f"Deleting {bucket_name}/{obj}")
        del_ok = True
    else:
        del_ok = ask(
            "These objects are not related to any existing resource: "
            + "".join([f"\n - {bucket_name}/{obj}" for obj in objects])
            + "\nDelete these orphaned objects?")

    if del_ok:
        s3_client, _, _ = s3.get_s3()
        for obj in objects:
            s3_client.delete_object(Bucket=bucket_name,
                                    Key=obj)
