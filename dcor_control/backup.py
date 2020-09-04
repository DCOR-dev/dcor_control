import pathlib
import subprocess as sp
import time


def make_backup():
    # put database backups on local storage, not on /data
    bpath = pathlib.Path("/backup") / time.strftime('backup_%Y-%m-%d_%H-%M-%S')
    bpath.mkdir(parents=True)
    dpath = bpath / "ckan.dump"
    sp.call("sudo -u postgres pg_dump --format=custom -d ckan_default > "
            + "{}".format(dpath), shell=True, stdout=sp.DEVNULL)
    assert dpath.exists()
    return dpath
