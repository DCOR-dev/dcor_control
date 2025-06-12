import click

from .. import prune as prune_mod


@click.command()
@click.option('--assume-yes', is_flag=True)
def prune(assume_yes=False):
    """Prune orphaned objects on S3"""
    # ask the user whether to search for orphaned files
    if assume_yes or click.confirm('Prune orphaned objects on S3?'):
        prune_mod.check_orphaned_s3_artifacts(
            assume_yes=assume_yes,
            older_than_days=0,
        )
