import click


from .server import status


@click.group()
def cli():
    pass


cli.add_command(status)
