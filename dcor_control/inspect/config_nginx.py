import logging
from dcor_shared.paths import get_nginx_config_path


logger = logging.getLogger(__name__)


def check_nginx(autocorrect=False):
    did_something = 0
    path_nginx = get_nginx_config_path()
    if path_nginx.exists():
        with open(path_nginx) as fd:
            lines = fd.readlines()
        for ii, line in enumerate(lines):
            if not line.strip() or line.startswith("#"):
                continue
            else:
                # TODO:
                # - check for DCOR-Aid client version
                #   (https://github.com/DCOR-dev/dcor_control/issues/24)
                pass
    else:
        logger.error(f"Nginx configuration file '{path_nginx}' not found. "
                     f"Not checking nginx configuration.")

    return did_something
