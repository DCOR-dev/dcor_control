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
        num_buckets = 0
        for bucket_name in s3.iter_buckets():
            num_buckets += 1
            bi = get_bucket_info(bucket_name)
            num_resources += bi["num_resources"]
            size_resources += bi["size_resources"]
            size_other += bi["size_other"]

        click.echo(f"S3 buckets:          {num_buckets}")
        click.echo(f"S3 resources number: {num_resources}")
        click.echo(f"S3 resources size:   {size_resources/1024**3:.0f} GiB")
        click.echo(f"S3 total size:       "
                   f"{(size_other + size_resources) / 1024**3:.0f} GiB")

        # Backup bucket
        try:
            bucket_prefix = get_ckan_config_option(
                "dcor_object_store.bucket_name").format(organization_id="")
            bbi = get_bucket_info(f"{bucket_prefix}000000000-backup",
                                  ret_object_keys=True)
        except BaseException:
            click.echo("Instance backup does not exist (yet).")
        else:
            click.echo(f"S3 instance backup number: {bbi['num_other']}")
            click.echo(f"S3 instance backup size:   "
                       f"{bbi['size_other']/1024**3:.0f} GiB")
            click.echo(f"S3 instance backup latest: {bbi['object_keys'][-1]}")


def get_bucket_info(bucket_name, ret_object_keys=False):
    s3_client, s3_session, s3_resource = s3.get_s3()
    num_resources = 0
    num_other = 0
    size_resources = 0
    size_other = 0
    object_keys = []

    kwargs = {"Bucket": bucket_name,
              "MaxKeys": 500
              }
    while True:
        resp = s3_client.list_objects_v2(**kwargs)

        for obj in resp.get("Contents", []):
            if ret_object_keys:
                object_keys.append(obj["Key"])

            if obj["Key"].startswith("resource/"):
                num_resources += 1
                size_resources += obj["Size"]
            else:
                num_other += 1
                size_other += obj["Size"]

        if not resp.get("IsTruncated"):
            break
        else:
            kwargs["ContinuationToken"] = resp.get(
                "NextContinuationToken")

    data = {
        "num_resources": num_resources,
        "num_other": num_other,
        "size_resources": size_resources,
        "size_other": size_other,
    }
    if ret_object_keys:
        data["object_keys"] = sorted(object_keys)
    return data
