import functools
import json
import logging
import os
import pathlib
import socket
import subprocess as sp

from dcor_shared.ckan import get_ckan_config_option, get_ckan_config_path
from dcor_shared.parse import ConfigOptionNotFoundError, parse_ini_config

from ..resources import resource_location
from .. import util

from . import common


logger = logging.getLogger(__name__)


def check_ckan_ini(dcor_site_config_dir=None, autocorrect=False):
    """Check custom ckan.ini server options

    This includes the contributions from
    - general options from resources/dcor_defaults.ini
    - as well as custom options in resources/server_options.json

    Custom options override general options.
    """
    did_something = 0
    srv_opts = get_expected_site_options(dcor_site_config_dir)

    if srv_opts is not None:
        dcor_opts = srv_opts["ckan.ini"]

        for key in dcor_opts:
            did_something += check_ckan_ini_option(
                key, dcor_opts[key], autocorrect=autocorrect)
    else:
        logger.info("Not checking ckan.ini, instance not managed via"
                    "`site_config_dir`")

    return did_something


def check_ckan_ini_option(key, value, autocorrect=False):
    """Check one server option"""
    did_something = 0
    ckan_ini = get_ckan_config_path()
    opt = get_actual_ckan_option(key)
    if opt != value:
        if autocorrect:
            print(f"Setting '{key}={value}' (was '{opt}').")
            change = True
        else:
            change = common.ask(f"'{key}' is '{opt}' but should be '{value}'")
        if change:
            ckan_cmd = f"ckan config-tool {ckan_ini} '{key}={value}'"
            sp.check_output(ckan_cmd, shell=True)
            did_something += 1
    return did_something


def check_dcor_theme_i18n_hack(autocorrect):
    """Generate the en_US locale and only *after* that set it in ckan.ini

    This will run the command::

       ckan -c /etc/ckan/default/ckan.ini dcor-theme-i18n-branding
    """
    did_something = 0
    ckan_ini = get_ckan_config_path()
    opt = get_actual_ckan_option("ckan.locale_default")
    if opt != "en_US":
        if autocorrect:
            print("Applying DCOR theme i18n hack")
            hack = True
        else:
            hack = common.ask("DCOR theme i18n is not setup")
        if hack:
            # apply hack
            ckan_cmd = f"ckan -c {ckan_ini} dcor-theme-i18n-branding"
            sp.check_output(ckan_cmd, shell=True)
            # set config option
            did_something += check_ckan_ini_option(
                "ckan.locale_default", "en_US", autocorrect=True)
    return did_something


def check_dcor_theme_main_css(autocorrect):
    """Generate dcor_main.css and patch a few template files

     This will run the command::

        ckan -c /etc/ckan/default/ckan.ini dcor-theme-main-css-branding
     """
    did_something = 0
    ckan_ini = get_ckan_config_path()
    opt = get_actual_ckan_option("ckan.theme")
    # TODO: Check whether the paths created by this script are set up correctly
    if opt != "dcor_theme_main/dcor_theme_main":
        if autocorrect:
            print("Applying DCOR theme main css and templating patches")
            replace_main = True
        else:
            replace_main = common.ask("DCOR theme CSS and patches not set-up")
        if replace_main:
            # apply hack
            ckan_cmd = f"ckan -c {ckan_ini} dcor-theme-main-css-branding"
            sp.check_output(ckan_cmd, shell=True)
            # set config option
            did_something += check_ckan_ini_option(
                key="ckan.theme",
                value="dcor_theme_main/dcor_theme_main",
                autocorrect=True)
            # apply patches
            ckan_cmd_2 = f"ckan -c {ckan_ini} dcor-patch-ckan-templates"
            sp.check_output(ckan_cmd_2, shell=True)

    return did_something


def get_actual_ckan_option(key):
    """Return the value of the given option in the current ckan.ini file"""
    try:
        opt = get_ckan_config_option(key)
    except ConfigOptionNotFoundError:
        opt = "NOT SET!"
    return opt


def get_dcor_site_config_dir(dcor_site_config_dir=None) -> pathlib.Path | None:
    """Return a local directory on disk containing the site's configuration

    The configuration directory is searched for in the following order:

    1. Path passed in dcor_site_config_dir
    2. Environment variable `DCOR_SITE_CONFIG_DIR`
    3. Matching sites in the `dcor_control.resources` directory

    If no configuration directory is found, return None.
    """
    if dcor_site_config_dir is not None:
        # passed via argument
        pass
    elif (env_cfg_dir := os.environ.get("DCOR_SITE_CONFIG_DIR")) is not None:
        # environment variable
        dcor_site_config_dir = env_cfg_dir
    else:
        # search registered sites
        for site_dir in sorted(resource_location.glob("site_dcor-*")):
            if is_site_config_dir_applicable(site_dir):
                dcor_site_config_dir = site_dir
                break
        else:
            logger.info(
                f"Could not determine the DCOR site configuration for "
                f"host '{socket.gethostname()}'. You did not specify the "
                f"`dcor_site_config_dir` keyword argument, the "
                f"`DCOR_SITE_CONFIG_DIR` environment variable is not set, "
                f"or there is no site configuration for this instance.")

    if dcor_site_config_dir:
        if not is_site_config_dir_applicable(dcor_site_config_dir):
            raise ValueError(
                f"The site configuration directory '{dcor_site_config_dir}' "
                f"is not applicable. Please check hostname and IP address.")

        return pathlib.Path(dcor_site_config_dir)
    else:
        return None


def get_expected_site_options(dcor_site_config_dir):
    """Return expected site config options for the specified site

    Returns a dictionary with "name", "requirements", and "ckan.ini".
    """
    dcor_site_config_dir = get_dcor_site_config_dir(dcor_site_config_dir)
    if dcor_site_config_dir is None:
        logger.info("Instance not managed via `site_config_dir`")
        return None

    cfg = json.loads((dcor_site_config_dir / "dcor_config.json").read_text())

    cfg["dcor_site_config_dir"] = dcor_site_config_dir
    # Store the information into permanent storage. We might reuse it.
    util.set_dcor_control_config("setup-identifier", cfg["name"])
    util.set_dcor_control_config("dcor-site-config-dir",
                                 str(dcor_site_config_dir))

    # Import DCOR default ckan.ini variables
    cfg_d = parse_ini_config(resource_location / "dcor_defaults.ini.template")
    for key, value in cfg_d.items():
        cfg["ckan.ini"].setdefault(key, value)

    # Branding: Determine extra template paths
    template_paths = []
    for pi in cfg.get("branding_paths", []):
        pp = (dcor_site_config_dir / pi).resolve() / "templates"
        if pp.exists():
            template_paths.append(str(pp))
    if template_paths:
        cfg["ckan.ini"]["extra_template_paths"] = ", ".join(template_paths)

    # Branding: Set extra public paths
    public_paths = []
    for pi in cfg.get("branding_paths", []):
        pp = (dcor_site_config_dir / pi).resolve() / "public"
        if pp.exists():
            public_paths.append(str(pp))
    if public_paths:
        cfg["ckan.ini"]["extra_public_paths"] = ", ".join(public_paths)

    # Fill in template variables
    update_expected_ckan_options_templates(cfg)

    return cfg


@functools.lru_cache()
def is_site_config_dir_applicable(dcor_site_config_dir):
    dcor_site_config_dir = pathlib.Path(dcor_site_config_dir)
    cfg = json.loads((dcor_site_config_dir / "dcor_config.json").read_text())
    # Determine which server we are on
    my_hostname = socket.gethostname()
    my_ip = get_ip()

    req = cfg["requirements"]
    ip = req.get("ip", "")
    if ip == "unknown":
        # The IP is unknown for this server.
        ip = my_ip
    hostname = req.get("hostname", "")
    return ip == my_ip and hostname == my_hostname


def update_expected_ckan_options_templates(cfg_dict, templates=None):
    """Update dict with templates in server_options.json"""
    if templates is None:
        templates = {
            "IP": [get_ip, []],
            "EMAIL": [util.get_dcor_control_config, ["email"]],
            "PGSQLPASS": [util.get_dcor_control_config, ["pgsqlpass"]],
            "HOSTNAME": [socket.gethostname, []],
            "DCOR_SITE_CONFIG_DIR": [cfg_dict.get, ["dcor_site_config_dir"]],
            "DCOR_SCHEMAS_PATH": [util.get_module_installation_path,
                                  ["ckanext.dcor_schemas"]],
        }

    for key in sorted(cfg_dict.keys()):
        item = cfg_dict[key]
        if isinstance(item, str):
            for tk in templates:
                tstr = f"<TEMPLATE:{tk}>"
                if item.count(tstr):
                    func, args = templates[tk]
                    item = item.replace(tstr, str(func(*args)))
            cfg_dict[key] = item
        elif isinstance(item, dict):
            # recurse into nested dicts
            update_expected_ckan_options_templates(item, templates=templates)


def get_ip():
    """Return IP address of current machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        myip = s.getsockname()[0]
    except BaseException:
        myip = '127.0.0.1'
    finally:
        s.close()
    return myip
