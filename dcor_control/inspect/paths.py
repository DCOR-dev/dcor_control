import os
import pathlib


from .common import get_ini_config_option


def get_ckan_config_path():
    default = "/etc/ckan/default/ckan.ini"
    return pathlib.Path(os.environ.get("CKAN_INI", default))


def get_ckan_storage_path():
    return pathlib.Path(get_ini_config_option(
        "ckan.storage_path",
        get_ckan_config_path()))


def get_ckan_webassets_path():
    return pathlib.Path(get_ini_config_option(
        "ckan.webassets.path",
        get_ckan_config_path()))


def get_dcor_depot_path():
    return pathlib.Path(get_ini_config_option(
        "ckanext.dcor_depot.depots_path",
        get_ckan_config_path()))


def get_dcor_users_depot_path():
    depot = get_dcor_depot_path()
    return depot / get_ini_config_option(
        "ckanext.dcor_depot.users_depot_name",
        get_ckan_config_path())


def get_nginx_config_path():
    return pathlib.Path("/etc/nginx/sites-enabled/ckan")


def get_supervisord_worker_config_path():
    return pathlib.Path("/etc/supervisor/conf.d/ckan-worker.conf")


def get_uwsgi_config_path():
    return pathlib.Path("/etc/ckan/default/ckan-uwsgi.ini")
