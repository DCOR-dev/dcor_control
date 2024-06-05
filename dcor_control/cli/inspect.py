import click
from dcor_shared import get_ckan_config_option, paths

from .. import inspect as inspect_mod


@click.command()
@click.option('--assume-yes', is_flag=True)
def inspect(assume_yes=False):
    """Inspect this DCOR installation"""
    cn = 0
    click.secho("Checking CKAN options...", bold=True)
    cn += inspect_mod.check_ckan_ini(autocorrect=assume_yes)

    click.secho("Checking beaker session secret...", bold=True)
    cn += inspect_mod.check_ckan_beaker_session_cookie_secret(
        autocorrect=assume_yes)

    click.secho("Checking www-data permissions...", bold=True)
    for path in [
        "/tmp/DCOR_generate_condensed",  # resource condense locks
        paths.get_ckan_storage_path(),
        paths.get_ckan_storage_path() / "resources",
        paths.get_dcor_users_depot_path(),
        paths.get_ckan_webassets_path(),
        get_ckan_config_option("ckanext.dc_serve.tmp_dir"),
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

    # Recursively make sure that www-data can upload things into storage
    cn += inspect_mod.check_permission(
        path=paths.get_ckan_storage_path() / "storage",
        user="www-data",
        mode_dir=0o755,
        mode_file=0o644,
        autocorrect=assume_yes,
        recursive=True)

    click.secho("Checking i18n hack...", bold=True)
    cn += inspect_mod.check_dcor_theme_i18n_hack(autocorrect=assume_yes)

    click.secho("Checking DCOR theme css branding...", bold=True)
    cn += inspect_mod.check_dcor_theme_main_css(autocorrect=assume_yes)

    click.secho("Checking ckan workers...", bold=True)
    cn += inspect_mod.check_supervisord(autocorrect=assume_yes)

    click.secho("Checking nginx configuration...", bold=True)
    cn += inspect_mod.check_nginx(cmbs="100G", autocorrect=assume_yes)

    click.secho("Checking uploader symlink patch...", bold=True)
    cn += inspect_mod.check_ckan_uploader_patch_to_support_symlinks(
        autocorrect=assume_yes)

    click.secho("Checking uwsgi configuration...", bold=True)
    cn += inspect_mod.check_uwsgi(harakiri=7200, autocorrect=assume_yes)

    if cn:
        inspect_mod.reload_supervisord()
        inspect_mod.reload_nginx()
    else:
        click.secho("No changes made.")

    # ask the user whether to search for orphaned files
    if assume_yes or click.confirm('Perform search for orphaned files?'):
        inspect_mod.check_orphaned_files(assume_yes=assume_yes)
        inspect_mod.check_orphaned_s3_artifacts(
            assume_yes=assume_yes,
            older_than_days=0,
        )

    click.secho('DONE', fg=u'green', bold=True)
