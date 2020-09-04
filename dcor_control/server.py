import collections.abc
import json
import pathlib
from pkg_resources import resource_filename
import socket

import appdirs
import click


def get_email():
    cpath = pathlib.Path(appdirs.user_config_dir("dcor_control"))
    cpath.mkdir(parents=True, exist_ok=True)
    epath = cpath / "email"
    if epath.exists():
        email = epath.read_text().strip()
    else:
        email = ""
    if not email:
        # Prompt user
        email = input("Please enter valid DCOR administrator email address: ")
        epath.write_text(email)
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


def fill_templates(adict):
    """Fill in templates in server_options.json"""
    for key in adict:
        item = adict[key]
        if isinstance(item, str):
            if item.count("<TEMPLATE:IP>"):  # fill in IP address
                adict[key] = item.replace("<TEMPLATE:IP>", get_ip())
            elif item.count("<TEMPLATE:EMAIL>"):
                adict[key] = item.replace("<TEMPLATE:EMAIL>", get_email())
        elif isinstance(item, dict):
            fill_templates(item)


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

    for setup in opt_dict["setups"]:
        req = setup["requirements"]
        ip = req.get("ip", my_ip)
        hostname = req.get("hostname", my_hostname)
        if ip == my_ip and hostname == my_hostname:
            break
    else:
        raise ValueError(
            "Could not determine server type;Not even fallback worked.")
    # Populate with includes
    for inc_key in setup["include"]:
        recursive_update_dict(setup, opt_dict["includes"][inc_key])
    # Fill in template variables
    fill_templates(setup)
    return setup


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
