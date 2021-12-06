import pathlib
import socket
import subprocess as sp
import time


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
    key installed and trusted, i.e.::

       gpg --import dcor_public.key
       gpg --edit-key 8FD98B2183B2C228
       $: trust
       $: 5  # (trust ultimately)
       $: quit

    Testing encryption with the key can be done with::

       gpg --output test.gpg --encrypt --recipient 8FD98B2183B2C228 afile

    Files can be decrypted with::

       gpg --output test --decrypt test.gpg
    """
    path_out.parent.mkdir(exist_ok=True, parents=True)
    path_out.parent.chmod(0o0700)
    sp.check_output("gpg --output '{}' --encrypt --recipient '{}' '{}'".format(
        path_out, key_id, path_in), shell=True)
    path_out.chmod(0o0400)
