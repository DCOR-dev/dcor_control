from dcor_shared.paths import get_uwsgi_config_path

from .common import ask


def check_uwsgi(harakiri, autocorrect=False):
    """Set harakiri timeout of uwsgi (important for data upload)

    Parameters
    ----------
    harakiri: int
        uwsgi timeout in minutes
    """
    path_uwsgi = get_uwsgi_config_path()
    with open(path_uwsgi) as fd:
        lines = fd.readlines()
    for ii, line in enumerate(lines):
        if line.startswith("harakiri"):
            value = int(line.split("=")[1])
            if value != harakiri:
                if autocorrect:
                    change = True
                    print("Setting UWSGI harakiri to {} min".format(harakiri))
                else:
                    change = ask(
                        "UWSGI timeout should be '{}' min".format(harakiri)
                        + ", but is '{}' min".format(value))
                if change:
                    lines[ii] = line.replace(str(value), str(harakiri))
                    with open(path_uwsgi, "w") as fd:
                        fd.writelines(lines)
