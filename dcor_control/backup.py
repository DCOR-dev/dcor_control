import pathlib
import subprocess as sp
import time


def db_backup():
    # put database backups on local storage, not on /data
    bpath = pathlib.Path("/backup") / time.strftime('backup_%Y-%m-%d_%H-%M-%S')
    bpath.mkdir(parents=True)
    dpath = bpath / "ckan.dump"
    sp.check_output("sudo -u postgres pg_dump --format=custom "
                    + "-d ckan_default > {}".format(dpath), shell=True)
    assert dpath.exists()
    return dpath
