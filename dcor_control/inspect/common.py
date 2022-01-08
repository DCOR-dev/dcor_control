import collections.abc
import pathlib
import grp
import os
import pwd
import stat


def ask(prompt):
    an = input(prompt + "; fix? [y/N]: ")
    return an.lower() == "y"


def check_permission(path, user=None, mode=None, recursive=False,
                     autocorrect=False):
    path = pathlib.Path(path)
    if recursive:
        for pp in path.rglob("*"):
            if pp.is_dir():
                check_permission(path=pp,
                                 user=user,
                                 mode=mode,
                                 recursive=False,
                                 autocorrect=autocorrect)
    if user is not None:
        uid = pwd.getpwnam(user).pw_uid
        gid = grp.getgrnam(user).gr_gid
    else:
        uid = None
        gid = None
    # Check if exists
    if not path.exists():
        if autocorrect:
            print("Creating '{}'".format(path))
            create = True
        else:
            create = ask("'{}' does not exist".format(path))
        if create:
            path.mkdir(parents=True)
            os.chmod(path, mode)
            if user is not None:
                os.chown(path, uid, gid)
    # Check mode
    pmode = stat.S_IMODE(path.stat().st_mode)
    if pmode != mode:
        if autocorrect:
            print("Changing mode of '{}' to '{}'".format(path, oct(mode)))
            change = True
        else:
            change = ask("Mode of '{}' is '{}', but ".format(path, oct(pmode))
                         + "should be '{}'".format(oct(mode)))
        if change:
            os.chmod(path, mode)
    # Check owner
    if user is not None:
        puid = path.stat().st_uid
        try:
            puidset = pwd.getpwuid(puid)
        except KeyError:
            pnam = "unknown"
        else:
            pnam = puidset.pw_name
        if puid != uid:
            if autocorrect:
                print("Changing owner of '{}' to '{}'".format(path, user))
                chowner = True
            else:
                chowner = ask("Owner of '{}' is ".format(path)
                              + "'{}', but should be '{}'".format(pnam, user))
            if chowner:
                os.chown(path, uid, gid)


def recursive_update_dict(d, u):
    """Updates dict `d` with `u` recursively"""
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = recursive_update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d
