import subprocess as sp

import click

from .. import inspect as inspect_mod


@click.command()
@click.option('--assume-yes', is_flag=True)
def inspsect(assume_yes=False):
    """Inspect this DCOR installation"""
    click.secho("Checking CKAN options...", bold=True)
    inspect_mod.check_ckan_ini(autocorrect=assume_yes)

    click.secho("Checking www-data permissions...", bold=True)
    for path in [
        "/tmp/DCOR_generate_condensed",  # resource condense locks
        inspect_mod.paths.get_ckan_storage_path(),
        inspect_mod.paths.get_ckan_storage_path() / "resources",
        inspect_mod.paths.get_dcor_depot_path(),
        inspect_mod.paths.get_dcor_users_depot_path(),
        inspect_mod.paths.get_ckan_webassets_path(),
    ]:
        inspect_mod.check_permission(
            path=path,
            user="www-data",
            mode=0o755,
            autocorrect=assume_yes)

    # Recursively make sure that www-data can upload things into storage
    inspect_mod.check_permission(
        path=inspect_mod.paths.get_ckan_storage_path() / "storage",
        user="www-data",
        mode=0o755,
        autocorrect=assume_yes,
        recursive=True)

    click.secho("Checking i18n hack...", bold=True)
    inspect_mod.check_dcor_theme_i18n_hack(autocorrect=assume_yes)

    click.secho("Checking DCOR theme css branding...", bold=True)
    inspect_mod.check_dcor_theme_main_css(autocorrect=assume_yes)

    click.secho("Checking ckan workers...", bold=True)
    inspect_mod.check_supervisord(autocorrect=assume_yes)

    click.secho("Checking nginx configuration...", bold=True)
    inspect_mod.check_nginx(cmbs="100G", autocorrect=assume_yes)

    click.secho("Checking uwsgi configuration...", bold=True)
    inspect_mod.check_uwsgi(harakiri=7200, autocorrect=assume_yes)

    click.secho("Reloading CKAN...", bold=True)
    sp.check_output("supervisorctl reload", shell=True)

    click.secho("Reloading nginx...", bold=True)
    sp.check_output("systemctl reload nginx", shell=True)

    # ask the user whether to search for orphaned files
    if click.confirm('Perform search for orphaned files?'):
        inspect_mod.check_orphaned_files(assume_yes=assume_yes)
