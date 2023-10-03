import socket

import click
from dcor_shared.paths import get_ckan_config_path

try:
    from dcor_shared import s3
except ImportError:
    s3 = None


from ..inspect.config_ckan import get_expected_ckan_options, get_ip


@click.command()
def status():
    """Display DCOR status"""
    srv_opts = get_expected_ckan_options()
    click.secho(f"DCOR installation: '{srv_opts['name']}'", bold=True)
    click.echo(f"IP Address: {get_ip()}")
    click.echo(f"Hostname: {socket.gethostname()}")
    click.echo(f"CKAN_INI: {get_ckan_config_path()}")

    if s3 is not None:
        # Object storage usage
        num_resources = 0
        size_resources = 0
        size_other = 0
        s3_client, s3_session, s3_resource = s3.get_s3()
        buckets = [b["Name"] for b in s3_client.list_buckets()["Buckets"]]
        for bucket in buckets:
            ctoken = ""
            while ctoken is not None:
                resp = s3_client.list_objects_v2(Bucket=bucket,
                                                 MaxKeys=1000,
                                                 ContinuationToken=ctoken)
                ctoken = resp.get("NextContinuationToken")
                for obj in resp.get("Contents"):
                    if obj["Key"].startswith("resource/"):
                        num_resources += 1
                        size_resources += obj["Size"]
                    else:
                        size_other += obj["Size"]
        click.echo(f"S3 buckets: {len(buckets)}")
        click.echo(f"S3 resources number: {num_resources}")
        click.echo(f"S3 resources size: {size_resources/1024**3:.0f} GB")
        click.echo(f"S3 total size: "
                   f"{(size_other + size_resources) / 1024**3:.0f} GB")
