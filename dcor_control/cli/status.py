import pathlib

import click
from dcor_shared.paths import get_ckan_config_path
from dcor_shared import get_ckan_config_option

try:
    from dcor_shared import s3
except ImportError:
    s3 = None


from ..inspect.config_ckan import get_expected_site_options, get_ip
from ..update import get_package_version
from ..util import get_dcor_control_config


@click.command()
def status():
    """Display DCOR status"""
    cfg = get_dcor_control_config("dcor-site-config-dir", interactive=False)
    if cfg is None:
        srv_name = get_ckan_config_option("ckan.site_title")
    else:
        dcor_site_config_dir = pathlib.Path(cfg)
        srv_opts = get_expected_site_options(dcor_site_config_dir)
        srv_name = f"{srv_opts['name']}"
    s3_endpoint = get_ckan_config_option("dcor_object_store.endpoint_url")

    click.secho(f"DCOR installation: {srv_name}", bold=True)
    click.echo(f"IP Address: {get_ip()}")
    click.echo(f"FQDN: {get_ckan_config_option('ckan.site_url')}")
    click.echo(f"S3 endpoint: {s3_endpoint}")
    click.echo(f"CKAN_INI: {get_ckan_config_path()}")

    for name in ["ckan                 ",
                 "ckanext.dc_log_view  ",
                 "ckanext.dc_serve     ",
                 "ckanext.dc_view      ",
                 "ckanext.dcor_depot   ",
                 "ckanext.dcor_schemas ",
                 "ckanext.dcor_theme   ",
                 "dcor_control         ",
                 "dcor_shared          "]:
        click.echo(f"Module {name} {get_package_version(name.strip())}")

    if s3 is not None:
        # Object storage usage
        num_resources = 0
        size_resources = 0
        size_other = 0
        s3_client, s3_session, s3_resource = s3.get_s3()
        buckets = [b["Name"] for b in s3_client.list_buckets()["Buckets"]]
        for bucket in buckets:
            kwargs = {"Bucket": bucket,
                      "MaxKeys": 500
                      }
            while True:
                resp = s3_client.list_objects_v2(**kwargs)

                for obj in resp.get("Contents", []):
                    if obj["Key"].startswith("resource/"):
                        num_resources += 1
                        size_resources += obj["Size"]
                    else:
                        size_other += obj["Size"]

                if not resp.get("IsTruncated"):
                    break
                else:
                    kwargs["ContinuationToken"] = resp.get(
                        "NextContinuationToken")

        click.echo(f"S3 buckets:          {len(buckets)}")
        click.echo(f"S3 resources number: {num_resources}")
        click.echo(f"S3 resources size:   {size_resources/1024**3:.0f} GB")
        click.echo(f"S3 total size:       "
                   f"{(size_other + size_resources) / 1024**3:.0f} GB")
