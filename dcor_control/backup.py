import pathlib
import socket
import subprocess as sp
import time

import click


def db_backup():
    # put database backups on local storage, not on /data
    bpath = pathlib.Path("/backup") / time.strftime('%Y-%m')
    bpath.mkdir(parents=True, exist_ok=True)
    bpath.chmod(0o0500)
    name = time.strftime('ckan_db_{}_%Y-%m-%d_%H-%M-%S.dump'.format(
        socket.gethostname()))
    dpath = bpath / name
    sp.check_output("sudo -u postgres pg_dump --format=custom "
                    + "-d ckan_default > {}".format(dpath), shell=True)
    assert dpath.exists()
    dpath.chmod(0o0400)
    return dpath


def gpg_encrypt(path_in, path_out, key_id):
    """Encrypt a file using gpg

    For this to work, you will have to have gpg installed and a working
    key installed and trusted, i.e.

    .. code::

       gpg --import dcor_public.key
       gpg --edit-key 8FD98B2183B2C228
       $: trust
       $: 5  # (trust ultimately)
       $: quit

    Testing encryption with the key can be done with

    .. code::

       gpg --output test.gpg --encrypt --recipient 8FD98B2183B2C228 afile

    Files can be decrypted with

    .. code::

       gpg --output test --decrypt test.gpg
    """
    path_out.parent.mkdir(exist_ok=True, parents=True)
    path_out.parent.chmod(0o0700)
    sp.check_output("gpg --output '{}' --encrypt --recipient '{}' '{}'".format(
        path_out, key_id, path_in), shell=True)
    path_out.chmod(0o0400)


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
