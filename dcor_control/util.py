import os
import pathlib

import appdirs


def get_dcor_control_config(name, custom_message=""):
    """Get (and at the same time store) dcor_control configuration keys"""
    cpath = pathlib.Path(appdirs.user_config_dir("dcor_control"))
    cpath.mkdir(parents=True, exist_ok=True)
    os.chmod(cpath, 0o700)
    epath = cpath / name
    if epath.exists():
        email = epath.read_text().strip()
    else:
        email = ""
    if not email:
        # Prompt user
        if custom_message:
            print(custom_message)
        email = input("Please enter '{}': ".format(name))
        epath.write_text(email)
    os.chmod(epath, 0o600)
    return email
