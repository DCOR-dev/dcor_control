import pathlib

import click
from dcor_shared import get_ckan_config_option, paths

from .common import reload_supervisord

from .. import inspect as inspect_mod


@click.command()
@click.option('--assume-yes', is_flag=True)
@click.option("--dcor-site-config-dir",
              type=click.Path(dir_okay=True,
                              file_okay=False,
                              resolve_path=True,
                              path_type=pathlib.Path),
              help="Path to a custom site configuration. For the main "
                   "sites in production, dcor_control comes with predefined "
                   "configurations (see the `resources` directory) and "
                   "the correct configuration can be inferred from e.g. "
                   "the hostname or IP address. If you are running a custom "
                   "DCOR instance, you may pass a path to your own "
                   "site configuration directory. You may also specify the "
                   "`DCOR_SITE_CONFIG_DIR` environment variable instead.")
def inspect(assume_yes=False, dcor_site_config_dir=None):
    """Inspect and optionally fix the DCOR installation"""
    cn = 0
    click.secho(
        f"Checking CKAN options ({paths.get_ckan_config_path()})...",
        bold=True)
    cn += inspect_mod.check_ckan_ini(dcor_site_config_dir=dcor_site_config_dir,
                                     autocorrect=assume_yes)

    click.secho("Checking www-data permissions...", bold=True)
    for path in [
        paths.get_ckan_storage_path(),
        paths.get_ckan_storage_path() / "resources",
        paths.get_ckan_webassets_path(),
        get_ckan_config_option("ckanext.dc_serve.tmp_dir"),
        get_ckan_config_option("ckanext.dcor_depot.tmp_dir"),
            ]:
        if path is not None:
            cn += inspect_mod.check_permission(
                path=path,
                user="www-data",
                mode_dir=0o755,
                mode_file=0o644,
                recursive=False,
                autocorrect=assume_yes)

    cn += inspect_mod.check_permission(
        path="/var/log/ckan",
        user="www-data",
        group="adm",
        mode_dir=0o755,
        mode_file=0o644,
        recursive=True,
        autocorrect=assume_yes)

    # Recursively make sure that www-data can upload things (e.g. images)
    # to the storage path
    cn += inspect_mod.check_permission(
        path=paths.get_ckan_storage_path() / "storage",
        user="www-data",
        mode_dir=0o755,
        mode_file=0o644,
        autocorrect=assume_yes,
        recursive=True)

    click.secho("Checking i18n hack...", bold=True)
    cn += inspect_mod.check_dcor_theme_i18n_hack(autocorrect=assume_yes)

    click.secho("Checking DCOR theme css branding and patches...", bold=True)
    cn += inspect_mod.check_dcor_theme_main_css(autocorrect=assume_yes)

    if cn:
        reload_supervisord()
    else:
        click.secho("No changes made.")

    click.secho('DONE', fg=u'green', bold=True)
