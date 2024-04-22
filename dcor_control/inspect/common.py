import collections.abc
import pathlib
import grp
import os
import pwd
import stat


def ask(prompt):
    an = input(prompt + "; fix? [y/N]: ")
    return an.lower() == "y"


def check_permission(path: str | pathlib.Path,
                     user: str = None,
                     group: str = None,
                     mode: oct = None,
                     recursive: bool = False,
                     autocorrect: bool = False):
    """Check permissions for a file or directory

    Parameters
    ----------
    path: str | pathlib.Path
        path to check for permissions
    user: str
        check ownership for user
    group: str
        check ownership for group
    mode: oct
        chmod code, e.g. `0o755`
    recursive: bool
        whether to recursively check for permissions
    autocorrect: bool
        whether to autocorrect permissions
    """
    path = pathlib.Path(path)
    if recursive and path.is_dir():
        for pp in path.rglob("*"):
            if pp.is_dir():
                check_permission(path=pp,
                                 user=user,
                                 mode=mode,
                                 recursive=False,
                                 autocorrect=autocorrect)
    if user is not None:
        uid = pwd.getpwnam(user).pw_uid
        gid = grp.getgrnam(group or user).gr_gid
    else:
        uid = None
        gid = None
    # Check if exists
    if not path.exists():
        if autocorrect:
            print(f"Creating '{path}'")
            create = True
        else:
            create = ask(f"'{path}' does not exist")
        if create:
            path.mkdir(parents=True)
            if mode is not None:
                os.chmod(path, mode)
            if user is not None:
                os.chown(path, uid, gid)
    # Check mode
    pmode = stat.S_IMODE(path.stat().st_mode)
    if mode is not None and pmode != mode:
        if autocorrect:
            print(f"Changing mode of '{path}' to '{oct(mode)}'")
            change = True
        else:
            change = ask(f"Mode of '{path}' is '{oct(pmode)}', "
                         f"but should be '{oct(mode)}'")
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
                print(f"Changing owner of '{path}' to '{user}'")
                chowner = True
            else:
                chowner = ask(f"Owner of '{path}' is '{pnam}', "
                              f"but should be '{user}'")
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
