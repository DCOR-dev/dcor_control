import collections.abc
import json
import os
import pathlib
from pkg_resources import resource_filename
import socket

import appdirs
import click


def get_config(name, custom_message=""):
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


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_server_options():
    """Determine the type of server and return the server options"""
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
            sn = get_config("setup-identifier", custom_message)
            if sn is not None:
                break
        else:
            raise ValueError("Could not get setup-identifier (tried 3 times)!")
        setup = cands[names.index(sn)]
    else:
        setup = cands[0]

    # Populate with includes
    for inc_key in setup["include"]:
        recursive_update_dict(setup, opt_dict["includes"][inc_key])
    # Fill in template variables
    process_ckan_ini_templates(setup)
    # Fill in branding variables
    process_ckan_ini_branding(setup)
    return setup


def process_ckan_ini_branding(ini_dict):
    """Set extra templates and public paths according to branding"""
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


def process_ckan_ini_templates(ini_dict):
    """Fill in templates in server_options.json"""
    templates = {
        "IP": [get_ip, []],
        "EMAIL": [get_config, ["email"]],
        "PGSQLPASS": [get_config, ["pgsqlpass"]],
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
            process_ckan_ini_templates(item)


def recursive_update_dict(d, u):
    """Updates dict `d` with `u` recursively"""
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = recursive_update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


@click.command()
def status():
    """Display DCOR status"""
    srv_opts = get_server_options()
    click.secho("DCOR installation: '{}'".format(srv_opts["name"]), bold=True)
    click.echo("IP Address: {}".format(get_ip()))
    click.echo("Hostname: {}".format(socket.gethostname()))
