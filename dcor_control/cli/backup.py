import pathlib

import click

from ..backup import db_backup, gpg_encrypt


@click.command()
@click.option('--key-id', default="8FD98B2183B2C228",
              help='The public gpg Key ID')
def encrypted_database_backup(key_id):
    """Create an asymmetrically encrypted database backup on /data/"""
    dpath = db_backup()
    name = "{}_{}.gpg".format(dpath.name, key_id)
    eout = pathlib.Path("/data/encrypted_db_dumps/") / dpath.parent.name / name
    gpg_encrypt(path_in=dpath, path_out=eout, key_id=key_id)
    click.secho("Created {}".format(eout), bold=True)
    click.secho('DONE', fg=u'green', bold=True)
