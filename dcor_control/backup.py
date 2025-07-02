import os
import pathlib
import pwd
import re
import shutil
import subprocess as sp
import time


# Check whether sudo is available, otherwise assume root permissions
SUDO = "sudo " if shutil.which("sudo") else ""


def db_backup(path="/backups", cleanup=True):
    """Perform CKAN database backup

    Parameters
    ----------
    path: str or pathlib.Path
        backup storage location; note that this should only be
        accessible to root
    cleanup: bool
        perform cleanup operations, which means deleting all but
        the latest 20 backups.
    """
    # put database backups on local storage, not on /data
    broot = pathlib.Path(path) / "database"
    broot.mkdir(parents=True, exist_ok=True)
    broot.chmod(0o0750)
    uid = pwd.getpwnam('postgres').pw_uid
    os.chown(broot, uid, 0)

    name = time.strftime(
        "backup_db_ckan_default_%Y-%m-%d_%H-%M-%S_dcor-control.pgc")
    dpath = broot / name

    sp.check_output(
        SUDO + "su - postgres -c "
        f'"pg_dump --format=custom -d ckan_default > {dpath}"',
        shell=True)
    assert dpath.exists()
    dpath.chmod(0o0400)

    if cleanup:
        delete_old_backups(
            backup_root=broot,
            latest_backup=dpath,
            regex=re.compile(
                r"^backup_db_ckan_default_(.*)_dcor-control\.pgc$"),
            )
    return dpath


def delete_old_backups(backup_root, latest_backup, regex, num=20):
    backup_root = pathlib.Path(backup_root)

    keep_list = [latest_backup]
    candidates = []

    # iterate in reverse order (newest first)
    for path in sorted(backup_root.glob("*"), reverse=True):
        if regex.match(path.name):
            candidates.append(path)
            if len(keep_list) <= num:
                keep_list.append(path)

    for path in candidates:
        if path not in keep_list:
            path.unlink()


def gpg_encrypt(path_in, path_out, key_id):
    """Encrypt a file using gpg

    For this to work, you will have to have gpg installed and a working
    key installed and trusted, i.e.::

       gpg --import dcor_public.key

    The following is optional, since we are using `--trust-model always`::

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
    sp.check_output(
        f"gpg "
        f"--output '{path_out}' "
        f"--encrypt "
        f"--trust-model always "
        f"--recipient '{key_id}' "
        f"'{path_in}'",
        shell=True)
    path_out.chmod(0o0400)
