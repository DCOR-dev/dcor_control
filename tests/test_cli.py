import os
import pathlib
import uuid

from click.testing import CliRunner
import pytest

from dcor_shared import get_ckan_config_option, s3

from dcor_control import cli
from dcor_control.cli import (
    backup, common, develop, inspect, reset, status, update
)


#: Some commands write to hard-coded locations such as `/backups`
requires_root = pytest.mark.skipif(os.geteuid() != 0,
                                   reason="requires root permissions")


@pytest.fixture
def mock_check_output(monkeypatch):
    calls = []

    def check_output(cmd, shell):
        calls.append(cmd)
        return b""

    for mod in [common, develop, reset, update]:
        monkeypatch.setattr(mod.sp, "check_output", check_output)
    return calls


@pytest.fixture
def no_supervisord(monkeypatch):
    reloads = []
    for mod in [develop, inspect, reset, update]:
        monkeypatch.setattr(mod, "reload_supervisord",
                            lambda: reloads.append(True))
    return reloads


def test_cli_main():
    result = CliRunner().invoke(cli.main, ["--help"])
    assert result.exit_code == 0
    for cmd in ["develop", "inspect", "reset", "status", "update",
                "encrypted-instance-backup"]:
        assert cmd in result.output


def test_is_supervisord_running(mock_check_output):
    assert common.is_supervisord_running()
    assert mock_check_output[0].endswith("supervisorctl status")


def test_reload_supervisord(monkeypatch, mock_check_output):
    monkeypatch.setattr(common, "is_supervisord_running", lambda: True)
    common.reload_supervisord()
    assert mock_check_output[0].endswith("supervisorctl reload")


def test_reload_supervisord_not_running(monkeypatch, capsys,
                                        mock_check_output):
    monkeypatch.setattr(common, "is_supervisord_running", lambda: False)
    common.reload_supervisord()
    assert not mock_check_output
    assert "supervisord not running" in capsys.readouterr().out


@requires_root
def test_cli_encrypted_instance_backup(monkeypatch, tmp_path):
    db_path = tmp_path / "db.pgc"
    db_path.write_text("database")
    storage_path = tmp_path / "storage"
    storage_path.mkdir()
    (storage_path / "image.png").write_text("image")

    def gpg_encrypt(path_in, path_out, key_id):
        path_out.write_bytes(path_in.read_bytes())

    monkeypatch.setattr(backup, "db_backup", lambda: db_path)
    monkeypatch.setattr(backup, "gpg_encrypt", gpg_encrypt)
    monkeypatch.setattr(
        backup, "get_ckan_config_option",
        lambda key: (str(storage_path) if key == "ckan.storage_path"
                     else get_ckan_config_option(key)))
    key_id = "PYTEST" + str(uuid.uuid4())[:8].upper()
    result = CliRunner().invoke(backup.encrypted_instance_backup,
                                ["--key-id", key_id])
    assert result.exit_code == 0, result.output
    eout, = pathlib.Path("/backups/instance-encrypted/").glob(
        f"*_{key_id}_dcor-control.tar.bz2.gpg")
    # the backup was uploaded to S3
    bucket_prefix = get_ckan_config_option(
        "dcor_object_store.bucket_name").format(organization_id="")
    info = status.get_bucket_info(f"{bucket_prefix}000000000-backup",
                                  ret_object_keys=True)
    assert any(key.endswith(eout.name) for key in info["object_keys"])


@pytest.mark.usefixtures("no_supervisord")
def test_cli_develop(monkeypatch, mock_check_output):
    migrated = []
    monkeypatch.setattr(develop, "migrate_to_editable",
                        lambda name: migrated.append(name))
    monkeypatch.setattr(develop.config_ckan, "check_ckan_ini_option",
                        lambda **kwargs: 0)
    result = CliRunner().invoke(develop.develop, ["--yes"])
    assert result.exit_code == 0, result.output
    assert "dcor_shared" in migrated
    assert "ckanext-dcor_schemas" in migrated
    assert mock_check_output[-1].endswith("dcor-theme-main-css-branding")


@requires_root
def test_migrate_to_editable(mock_check_output):
    wd = os.getcwd()
    develop.migrate_to_editable("dcor_peter")
    assert mock_check_output[0] == \
        "git clone https://github.com/DCOR-dev/dcor_peter"
    assert mock_check_output[1].endswith("install -e /dcor-repos/dcor_peter")
    assert os.getcwd() == wd


def test_cli_inspect(monkeypatch, no_supervisord):
    checked = []
    monkeypatch.setattr(inspect.inspect_mod, "check_ckan_ini",
                        lambda **kwargs: 0)
    monkeypatch.setattr(inspect.inspect_mod, "check_permission",
                        lambda path, **kwargs: checked.append(str(path)) or 0)
    monkeypatch.setattr(inspect.inspect_mod, "check_dcor_theme_i18n_hack",
                        lambda autocorrect: 0)
    monkeypatch.setattr(inspect.inspect_mod, "check_dcor_theme_main_css",
                        lambda autocorrect: 1)
    result = CliRunner().invoke(inspect.inspect, ["--assume-yes"])
    assert result.exit_code == 0, result.output
    assert "/var/log/ckan" in checked
    # a change was made, so CKAN is reloaded
    assert no_supervisord == [True]


@pytest.mark.usefixtures("no_supervisord")
def test_cli_reset(monkeypatch, tmp_path, mock_check_output,
                   dcor_control_config_dir):
    dcor_control_config_dir.mkdir()
    result = CliRunner().invoke(
        reset.reset, ["--cache", "--search-index", "--control", "--yes"])
    assert result.exit_code == 0, result.output
    assert mock_check_output[0].endswith("asset clean")
    assert mock_check_output[1].endswith("search-index clear")
    assert not dcor_control_config_dir.exists()


@pytest.mark.usefixtures("no_supervisord")
def test_cli_reset_zombie_users(monkeypatch, tmp_path, mock_check_output):
    monkeypatch.setattr(reset, "db_backup", lambda: tmp_path / "backup.pgc")
    result = CliRunner().invoke(
        reset.reset, ["--zombie-users", "--keep-user", "peter", "--yes"])
    assert result.exit_code == 0, result.output
    assert "Created backup" in result.output
    cmd, = mock_check_output
    assert "list-zombie-users | grep -v ^peter$ | xargs" in cmd


def test_cli_reset_database_and_datasets():
    result = CliRunner().invoke(
        reset.reset, ["--database", "--datasets", "--yes"])
    assert isinstance(result.exception, ValueError)


@pytest.mark.usefixtures("no_supervisord")
def test_cli_update(monkeypatch, mock_check_output):
    updated = []
    monkeypatch.setattr(update, "update_package",
                        lambda name: updated.append(name))
    result = CliRunner().invoke(update.update, ["--yes"])
    assert result.exit_code == 0, result.output
    assert updated[0] == "dcor_shared"
    assert updated[-1] == "dcor_control"
    assert mock_check_output[0].endswith("install --upgrade pip")


def test_get_bucket_info(tmp_path):
    bucket_name = f"test-circle-{uuid.uuid4()}"
    path = tmp_path / "file.txt"
    path.write_text("0123456789")
    for object_name in ["resource/abc/def/123", "condensed/abc/def/123",
                        "preview/abc/def/123"]:
        s3.upload_file(bucket_name=bucket_name,
                       object_name=object_name,
                       path=path)
    info = status.get_bucket_info(bucket_name, ret_object_keys=True)
    assert info == {
        "num_resources": 1,
        "num_other": 2,
        "size_resources": 10,
        "size_other": 20,
        "object_keys": ["condensed/abc/def/123", "preview/abc/def/123",
                        "resource/abc/def/123"],
    }


@pytest.mark.usefixtures("dcor_control_config_dir")
def test_cli_status(monkeypatch):
    monkeypatch.setattr(status, "get_package_version", lambda name: "1.0")
    result = CliRunner().invoke(status.status)
    assert result.exit_code == 0, result.output
    assert "DCOR installation:" in result.output
    assert "Module dcor_shared           1.0" in result.output
    assert "S3 buckets:" in result.output
