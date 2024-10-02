from dcor_shared.paths import get_nginx_config_path


def check_nginx(autocorrect=False):
    did_something = 0
    path_nginx = get_nginx_config_path()
    with open(path_nginx) as fd:
        lines = fd.readlines()
    for ii, line in enumerate(lines):
        if not line.strip() or line.startswith("#"):
            continue
        else:
            # TODO:
            # - check for DCOR-Aid client version
            pass

    return did_something
