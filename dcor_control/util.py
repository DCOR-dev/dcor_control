import os
import pathlib

import appdirs


def get_dcor_control_config(name, custom_message="", interactive=True):
    """Get (and at the same time store) dcor_control configuration keys"""
    cpath = pathlib.Path(appdirs.user_config_dir("dcor_control"))
    cpath.mkdir(parents=True, exist_ok=True)
    os.chmod(cpath, 0o700)
    data_path = cpath / name
    if data_path.exists():
        data = data_path.read_text().strip()
    else:
        data = ""
    if not data:
        if interactive:
            # Prompt user
            if custom_message:
                print(custom_message)
            data = input("Please enter '{}': ".format(name))
            data_path.write_text(data)
        else:
            raise KeyError(f"Configuration '{name}' not found/set. Maybe "
                           f"running `dcor inspect` helps?")
    os.chmod(data_path, 0o600)
    return data


def set_dcor_control_config(name, data):
    """Get (and at the same time store) dcor_control configuration keys"""
    cpath = pathlib.Path(appdirs.user_config_dir("dcor_control"))
    cpath.mkdir(parents=True, exist_ok=True)
    os.chmod(cpath, 0o700)
    data_path = cpath / name
    data_path.write_text(data)
    os.chmod(data_path, 0o600)
    return data
