from __future__ import annotations

import collections.abc
import pathlib
import grp
import os
import pwd
import stat
import warnings


def ask(prompt):
    an = input(prompt + "; fix? [y/N]: ")
    return an.lower() == "y"


def check_permission(path: str | pathlib.Path,
                     user: str = None,
                     group: str = None,
                     mode_dir: oct = None,
                     mode_file: oct = None,
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
        check ownership for group, defaults to `user`
    mode_dir: oct
        chmod code, e.g. `0o755`
    mode_file: oct
        chmod code, e.g. `0o755`
    recursive: bool
        whether to recursively check for permissions
    autocorrect: bool
        whether to autocorrect permissions
    """
    did_something = 0
    group = group or user
    uid = pwd.getpwnam(user).pw_uid if user is not None else None
    gid = grp.getgrnam(group).gr_gid if group is not None else None

    path = pathlib.Path(path)

    if path.is_file():
        mode = mode_file
    elif path.is_dir():
        mode = mode_dir
        if recursive:
            for pp in path.glob("*"):
                did_something += check_permission(
                    path=pp,
                    user=user,
                    group=group,
                    mode_dir=mode_dir,
                    mode_file=mode_file,
                    recursive=recursive,
                    autocorrect=autocorrect
                )
    else:
        # create a directory
        mode = mode_dir
        if autocorrect:
            print(f"Creating directory '{path}'")
            create = True
        else:
            create = ask(f"Directory '{path}' does not exist")
        if create:
            did_something += 1
            path.mkdir(parents=True)
            if mode is not None:
                os.chmod(path, mode)
            if user is not None:
                try:
                    os.chown(path, uid, gid)
                except BaseException:
                    warnings.warn(
                        f"Failed to set ownership '{uid}:{gid}' for '{path}'")

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
            did_something += 1
            os.chmod(path, mode)

    # Check owner
    if uid is not None and gid is not None:
        puid = path.stat().st_uid
        pgid = path.stat().st_gid
        if puid != uid or pgid != gid:
            # Get current group name
            try:
                pgidset = grp.getgrgid(pgid)
            except BaseException:
                pgrp = "unknown"
            else:
                pgrp = pgidset.gr_name
            # Get current user name
            try:
                puidset = pwd.getpwuid(puid)
            except BaseException:
                pusr = "unknown"
            else:
                pusr = puidset.pw_name
            # Perform the change
            if autocorrect:
                print(f"Changing owner of '{path}' to '{user}:{group}'")
                chowner = True
            else:
                chowner = ask(f"Owner of '{path}' is '{pusr}:{pgrp}', "
                              f"but should be '{user}:{group}'")
            if chowner:
                try:
                    os.chown(path, uid, gid)
                except BaseException:
                    warnings.warn(
                        f"Failed to set ownership '{uid}:{gid}' for '{path}'")
                else:
                    did_something += 1

    return did_something


def recursive_update_dict(d, u):
    """Updates dict `d` with `u` recursively"""
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = recursive_update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d
