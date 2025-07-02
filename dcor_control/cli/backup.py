import pathlib
import re
import tarfile
import time

import click

from dcor_shared import get_ckan_config_option, s3

from ..backup import db_backup, delete_old_backups, gpg_encrypt


@click.command()
@click.option('--key-id', default="2B4B066FFE3D288E",
              help='The public gpg Key ID')
@click.option('--skip-s3', is_flag=True,
              help='Do not upload the instance backup to S3')
def encrypted_instance_backup(key_id, skip_s3=False):
    """Create an asymmetrically encrypted backup of this DCOR instance

    The backup file contains the CKAN database as well as the contents
    of `/data`.

    The backup is stored in `/backups/instance-encrypted/` and uploaded
    to the S3 object storage to the `{dcor_object_store.bucket_name}-backup`
    bucket if `--skip-s3` is not specified.

    To get a list of available signatures on your system, run
    `gpg --list-signatures`.
    You can import and export keys using `gpg --import filename.key`
    and `gpg --export KEYID > filename.key`.
    See :func:`.gpg_encrypt` for more information.
    """
    now = time.strftime("%Y-%m-%d_%H-%M-%S")

    # Get database backup
    click.secho("Creating database backup...")
    db_path = db_backup()

    # Create a tar.bz2 file that contains the contents of /data and `dp_path`.
    click.secho("Creating instance backup...")
    storage_path = pathlib.Path(get_ckan_config_option("ckan.storage_path"))
    droot = pathlib.Path("/backups/instance/")
    droot.mkdir(parents=True, exist_ok=True)
    dpath = droot / f"backup_instance_{now}_{key_id}_dcor-control.tar.bz2"
    with tarfile.open(dpath, "w:bz2") as z:
        z.add(db_path)
        z.add(storage_path)

    # create encrypted version
    click.secho("Encrypting instance backup...")
    eroot = pathlib.Path("/backups/instance-encrypted/")
    eroot.mkdir(parents=True, exist_ok=True)
    eout = eroot / (dpath.name + ".gpg")
    gpg_encrypt(path_in=dpath, path_out=eout, key_id=key_id)
    click.secho(f"Created {eout}", bold=True)

    if not skip_s3:
        click.secho("Uploading to S3...")
        bucket_prefix = get_ckan_config_option(
            "dcor_object_store.bucket_name").format(organization_id="")
        bucket_name = bucket_prefix + "000000000-backup"
        s3.require_bucket(bucket_name)
        s3.upload_file(bucket_name=bucket_name,
                       object_name=f"{now[:4]}/{now[5:7]}/{eout.name}",
                       path=eout)

    click.secho("Cleaning up...")
    delete_old_backups(
        backup_root=droot,
        latest_backup=dpath,
        regex=re.compile(
            f"^backup_instance_(.*)_{key_id}_dcor-control\\.tar.bz2$"),
        num=10)

    delete_old_backups(
        backup_root=eroot,
        latest_backup=eout,
        regex=re.compile(
            f"^backup_instance_(.*)_{key_id}_dcor-control\\.tar.bz2.gpg$"),
        num=10)

    click.secho('DONE', fg=u'green', bold=True)
