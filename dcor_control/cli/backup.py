import pathlib
import socket

import click

from ..backup import db_backup, delete_old_backups, gpg_encrypt


@click.command()
@click.option('--key-id', default="8FD98B2183B2C228",
              help='The public gpg Key ID')
def encrypted_database_backup(key_id):
    """Create an asymmetrically encrypted database backup on /data/

    You can import and export keys using `gpg --import fielname.key`
    and `gpg --export KEYID > filename.key`.
    The key specified must be trusted ultimately. To do this run
    `gpg --edit-key KEYID` and then type `trust`.
    """
    dpath = db_backup()
    name = "{}_{}.gpg".format(dpath.name, key_id)
    eroot = pathlib.Path("/data/encrypted_db_dumps/")
    eout = eroot / dpath.parent.name / name
    gpg_encrypt(path_in=dpath, path_out=eout, key_id=key_id)
    click.secho("Created {}".format(eout), bold=True)

    click.secho("Cleaning up...")
    delete_old_backups(backup_root=eroot,
                       latest_backup=eout,
                       stem=f"ckan_db_{socket.gethostname()}",
                       suffix=".gpg")
    click.secho('DONE', fg=u'green', bold=True)
