import pathlib

CKANINI = "/etc/ckan/default/ckan.ini"


class ConfigOptionNotFoundError(BaseException):
    pass


def parse_config_options(ini):
    opt_dict = {}
    with open(ini) as fd:
        for line in fd.readlines():
            line = line.strip()
            if line.startswith("#") or line.startswith("["):
                continue
            elif line.count("="):
                key, value = line.split("=", 1)
                opt_dict[key.strip()] = value.strip()
    return opt_dict


def get_config_option(option, ini=CKANINI):
    opt_dict = parse_config_options(ini)
    if option in opt_dict:
        value = opt_dict[option]
    else:
        raise ConfigOptionNotFoundError("Could not find '{}'!".format(option))
    return value


def get_depot_path():
    return pathlib.Path(get_config_option("ckanext.dcor_depot.depots_path"))


def get_storage_path():
    return pathlib.Path(get_config_option("ckan.storage_path"))


def get_users_depot_path():
    depot = get_depot_path()
    return depot / get_config_option("ckanext.dcor_depot.users_depot_name")
