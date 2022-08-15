from datetime import date, timedelta
import os
import pathlib
import socket
import subprocess as sp
import time


def db_backup(path="/backup", cleanup=True):
    """Perform CKAN database backup

    Parameters
    ----------
    path: str or pathlib.Path
        backup storage location; note that this should only be
        accessible to root
    cleanup: bool
        perform cleanup operations, which means
        - keep a daily backup for the past two weeks
        - keep a monthly backup for the past year
        - keep a yearly backup for the past ten years
        - delete all other backups
    """
    # put database backups on local storage, not on /data
    broot = pathlib.Path(path)
    bpath = broot / time.strftime('%Y-%m')
    bpath.mkdir(parents=True, exist_ok=True)
    bpath.chmod(0o0500)
    name = time.strftime('ckan_db_{}_%Y-%m-%d_%H-%M-%S.dump'.format(
        socket.gethostname()))
    dpath = bpath / name
    sp.check_output("sudo -u postgres pg_dump --format=custom "
                    + "-d ckan_default > {}".format(dpath), shell=True)
    assert dpath.exists()
    dpath.chmod(0o0400)

    if cleanup:
        delete_old_backups(backup_root=broot,
                           latest_backup=dpath,
                           stem=f"ckan_db_{socket.gethostname()}",
                           suffix=".dump")
    return dpath


def delete_old_backups(backup_root, latest_backup, stem, suffix):
    keep_list = [latest_backup]
    # keep a daily backup for the past two weeks
    for ii in range(1, 14):
        keep_list.append(get_backup_file_from(
            backup_root,
            days_ago=ii,
            time_stem=f'{stem}_%Y-%m-%d_*{suffix}'))
    # keep a monthly backup for the past month
    for ii in range(1, 12):
        keep_list.append(get_backup_file_from(
            backup_root,
            months_ago=ii,
            time_stem=f'{stem}_%Y-%m-*{suffix}'))
    # keep a yearly backup for the past ten years
    for ii in range(1, 10):
        keep_list.append(get_backup_file_from(
            backup_root,
            years_ago=ii,
            time_stem=f'{stem}_%Y-*{suffix}'))
    if len(keep_list) > 2:
        empty_dirs = []
        for pp in backup_root.rglob(f"{stem}*{suffix}"):
            if pp not in keep_list:
                print(f"Removing {pp}")
                pp.unlink()
                if not (list(pp.parent.rglob("*"))):
                    # remove empty dirs
                    empty_dirs.append(pp.parent)
        for pd in empty_dirs:
            os.rmdir(pd)


def get_backup_file_from(path, time_stem, days_ago=0, months_ago=0,
                         years_ago=0):
    today = date.today()
    if days_ago:
        time_tuple = (today - timedelta(days_ago)).timetuple()
    elif months_ago:
        the_day = today.replace(day=1)
        for _ in range(months_ago):
            last_month = the_day - timedelta(days=1)
            the_day = last_month.replace(day=1)
        time_tuple = the_day.timetuple()
    elif years_ago:
        first = today.replace(day=1)
        last_year = first.replace(year=today.year - years_ago)
        time_tuple = last_year.timetuple()
    else:
        raise ValueError("Must specify past kwargs")
    search_path = time.strftime(time_stem, time_tuple)
    results = sorted(path.rglob(search_path))
    if results:
        return results[0]


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
