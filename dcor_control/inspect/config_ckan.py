import json
import pathlib
from pkg_resources import resource_filename
import socket
import subprocess as sp

from dcor_shared.paths import get_ckan_config_option, get_ckan_config_path
from dcor_shared.parse import ConfigOptionNotFoundError, parse_ini_config

from .. import util

from . import common


def check_ckan_ini(autocorrect=False):
    """Check custom ckan.ini server options

    This includes the contributions from
    - general options from resources/dcor_options.ini
    - as well as custom options in resources/server_options.json

    Custom options override general options.
    """
    custom_opts = get_expected_ckan_options()["ckan.ini"]
    general_opts = parse_ini_config(
        resource_filename("dcor_control.resources", "dcor_options.ini"))

    general_opts.update(custom_opts)

    for key in general_opts:
        check_ckan_ini_option(key, general_opts[key], autocorrect=autocorrect)


def check_ckan_ini_option(key, value, autocorrect=False):
    """Check one server option"""
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


def check_dcor_theme_i18n_hack(autocorrect):
    """Generate the en_US locale and only *after* that set it in ckan.ini

    This will run the command::

       ckan -c /etc/ckan/default/ckan.ini dcor-theme-i18n-branding
    """
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
            check_ckan_ini_option("ckan.locale_default", "en_US",
                                  autocorrect=True)


def check_dcor_theme_main_css(autocorrect):
    """Generate dcor_main.css

     This will run the command::

        ckan -c /etc/ckan/default/ckan.ini dcor-theme-main-css-branding
     """
    ckan_ini = get_ckan_config_path()
    opt = get_actual_ckan_option("ckan.main_css")
    if opt != "/base/css/dcor_main.css":
        if autocorrect:
            print("Applying DCOR theme main css")
            replace_main = True
        else:
            replace_main = common.ask("DCOR theme dcor_main.css is not setup")
        if replace_main:
            # apply hack
            ckan_cmd = f"ckan -c {ckan_ini} dcor-theme-main-css-branding"
            sp.check_output(ckan_cmd, shell=True)
            # set config option
            check_ckan_ini_option("ckan.main_css", "/base/css/dcor_main.css",
                                  autocorrect=True)


def get_actual_ckan_option(key):
    """Return the value of the given option in the current ckan.ini file"""
    try:
        opt = get_ckan_config_option(key)
    except ConfigOptionNotFoundError:
        opt = "NOT SET!"
    return opt


def get_expected_ckan_options():
    """Return expected ckan.ini options for the current host"""
    # Load the json data
    opt_path = resource_filename("dcor_control.resources",
                                 "server_options.json")
    with open(opt_path) as fd:
        opt_dict = json.load(fd)
    # Determine which server we are on
    my_hostname = socket.gethostname()
    my_ip = get_ip()

    cands = []
    for setup in opt_dict["setups"]:
        req = setup["requirements"]
        ip = req.get("ip", "")
        hostname = req.get("hostname", "")
        if ip == my_ip and hostname == my_hostname:
            # perfect match
            cands = [setup]
            break
        elif ip or hostname:
            # no match
            continue
        else:
            # fallback setup
            cands.append(setup)
    if len(cands) == 0:
        raise ValueError("No fallback setups?")
    if len(cands) != 1:
        names = [setup["name"] for setup in cands]
        custom_message = "Valid setup-identifiers: {}".format(
                         ", ".join(names))
        for _ in range(3):
            sn = util.get_dcor_control_config("setup-identifier",
                                              custom_message)
            if sn is not None:
                break
        else:
            raise ValueError("Could not get setup-identifier (tried 3 times)!")
        setup = cands[names.index(sn)]
    else:
        setup = cands[0]

    # Populate with includes
    for inc_key in setup["include"]:
        common.recursive_update_dict(setup, opt_dict["includes"][inc_key])
    # Fill in template variables
    update_expected_ckan_options_templates(setup)
    # Fill in branding variables
    update_expected_ckan_options_branding(setup)
    return setup


def update_expected_ckan_options_branding(ini_dict):
    """Update dict with templates and public paths according to branding"""
    brands = ini_dict["branding"]
    # Please not the dcor_control must be an installed package for
    # this to work (no egg or somesuch).
    templt_paths = []
    public_paths = []
    for brand in brands:
        template_dir = resource_filename("dcor_control.resources.branding",
                                         "templates_{}".format(brand))
        if pathlib.Path(template_dir).exists():
            templt_paths.append(template_dir)
        public_dir = resource_filename("dcor_control.resources.branding",
                                       "public_{}".format(brand))
        if pathlib.Path(public_dir).exists():
            public_paths.append(public_dir)
    if templt_paths:
        ini_dict["ckan.ini"]["extra_template_paths"] = ", ".join(templt_paths)
    if public_paths:
        ini_dict["ckan.ini"]["extra_public_paths"] = ", ".join(public_paths)


def update_expected_ckan_options_templates(ini_dict):
    """Update dict with templates in server_options.json"""
    templates = {
        "IP": [get_ip, []],
        "EMAIL": [util.get_dcor_control_config, ["email"]],
        "PGSQLPASS": [util.get_dcor_control_config, ["pgsqlpass"]],
        "HOSTNAME": [socket.gethostname, []],
        "PATH_BRANDING": [resource_filename, ["dcor_control.resources",
                                              "branding"]],
    }

    for key in sorted(ini_dict.keys()):
        item = ini_dict[key]
        if isinstance(item, str):
            for tk in templates:
                tstr = "<TEMPLATE:{}>".format(tk)
                if item.count(tstr):
                    func, args = templates[tk]
                    item = item.replace(tstr, func(*args))
            ini_dict[key] = item
        elif isinstance(item, dict):
            # recurse into nested dicts
            update_expected_ckan_options_templates(item)


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
