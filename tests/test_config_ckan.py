import json
import socket

import pytest

from dcor_control import util
from dcor_control.inspect import config_ckan
from dcor_shared.parse import ConfigOptionNotFoundError


def make_site_config_dir(path, hostname=None):
    """Create a site configuration directory that matches this machine"""
    path.mkdir()
    (path / "branding" / "templates").mkdir(parents=True)
    (path / "branding" / "public").mkdir(parents=True)
    (path / "dcor_config.json").write_text(json.dumps({
        "name": "pytest-site",
        "requirements": {
            "ip": "unknown",
            "hostname": hostname or socket.gethostname()},
        "branding_paths": ["branding"],
        "ckan.ini": {
            "ckan.site_title": "Pytest <TEMPLATE:HOSTNAME>",
            "ckan.site_url": "http://<TEMPLATE:IP>",
        },
    }))
    return path


@pytest.fixture
def mock_check_output(monkeypatch):
    calls = []
    monkeypatch.setattr(config_ckan.sp, "check_output",
                        lambda cmd, shell: calls.append(cmd))
    return calls


@pytest.fixture
def ckan_options(monkeypatch):
    """Pretend to be ckan.ini with options stored in a dictionary"""
    options = {}

    def get_ckan_config_option(key):
        if key not in options:
            raise ConfigOptionNotFoundError(key)
        return options[key]

    monkeypatch.setattr(config_ckan, "get_ckan_config_option",
                        get_ckan_config_option)
    return options


def test_get_actual_ckan_option(ckan_options):
    ckan_options["ckan.site_title"] = "DCOR"
    assert config_ckan.get_actual_ckan_option("ckan.site_title") == "DCOR"
    assert config_ckan.get_actual_ckan_option("ckan.nope") == "NOT SET!"


def test_check_ckan_ini_option(ckan_options, mock_check_output):
    ckan_options["ckan.site_title"] = "DCOR"
    assert config_ckan.check_ckan_ini_option("ckan.site_title", "DCOR") == 0
    assert not mock_check_output
    assert config_ckan.check_ckan_ini_option(
        "ckan.site_title", "Peter", autocorrect=True) == 1
    cmd, = mock_check_output
    assert cmd.startswith("ckan config-tool ")
    assert cmd.endswith("'ckan.site_title=Peter'")


def test_check_ckan_ini_option_declined(monkeypatch, ckan_options,
                                        mock_check_output):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert config_ckan.check_ckan_ini_option("ckan.site_title", "Peter") == 0
    assert not mock_check_output


def test_check_dcor_theme_i18n_hack(ckan_options, mock_check_output):
    ckan_options["ckan.locale_default"] = "en_US"
    assert config_ckan.check_dcor_theme_i18n_hack(autocorrect=True) == 0
    assert not mock_check_output
    ckan_options["ckan.locale_default"] = "en"
    assert config_ckan.check_dcor_theme_i18n_hack(autocorrect=True) == 1
    assert mock_check_output[0].endswith("dcor-theme-i18n-branding")
    assert mock_check_output[1].endswith("'ckan.locale_default=en_US'")


def test_check_dcor_theme_main_css(ckan_options, mock_check_output):
    ckan_options["ckan.theme"] = "dcor_theme_main/dcor_theme_main"
    assert config_ckan.check_dcor_theme_main_css(autocorrect=True) == 0
    assert not mock_check_output
    ckan_options["ckan.theme"] = "css/main"
    assert config_ckan.check_dcor_theme_main_css(autocorrect=True) == 1
    assert mock_check_output[0].endswith("dcor-theme-main-css-branding")
    assert mock_check_output[1].endswith(
        "'ckan.theme=dcor_theme_main/dcor_theme_main'")
    assert mock_check_output[2].endswith("dcor-patch-ckan-templates")


def test_get_dcor_site_config_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("DCOR_SITE_CONFIG_DIR", raising=False)
    site_dir = make_site_config_dir(tmp_path / "site")
    assert config_ckan.get_dcor_site_config_dir(site_dir) == site_dir
    monkeypatch.setenv("DCOR_SITE_CONFIG_DIR", str(site_dir))
    assert config_ckan.get_dcor_site_config_dir() == site_dir


def test_get_dcor_site_config_dir_not_applicable(tmp_path):
    site_dir = make_site_config_dir(tmp_path / "site",
                                    hostname="not-this-host")
    with pytest.raises(ValueError, match="is not applicable"):
        config_ckan.get_dcor_site_config_dir(site_dir)


def test_get_dcor_site_config_dir_none(monkeypatch):
    monkeypatch.delenv("DCOR_SITE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(config_ckan, "is_site_config_dir_applicable",
                        lambda path: False)
    assert config_ckan.get_dcor_site_config_dir() is None
    assert config_ckan.get_expected_site_options(None) is None


def test_get_expected_site_options(tmp_path, dcor_control_config_dir):
    site_dir = make_site_config_dir(tmp_path / "site")
    util.set_dcor_control_config("pgsqlpass", "s3cr3t")
    cfg = config_ckan.get_expected_site_options(site_dir)
    assert cfg["name"] == "pytest-site"
    assert cfg["dcor_site_config_dir"] == site_dir
    opts = cfg["ckan.ini"]
    # templates are filled in
    assert opts["ckan.site_title"] == f"Pytest {socket.gethostname()}"
    assert opts["ckan.site_url"] == f"http://{config_ckan.get_ip()}"
    # branding paths
    assert opts["extra_template_paths"] == str(
        site_dir / "branding" / "templates")
    assert opts["extra_public_paths"] == str(
        site_dir / "branding" / "public")
    # defaults from dcor_defaults.ini.template
    assert "ckan.plugins" in opts
    assert opts["sqlalchemy.url"] == \
        "postgresql://ckan_default:s3cr3t@localhost/ckan_default"
    # setup identifier is stored
    assert (dcor_control_config_dir / "setup-identifier").read_text() \
        == "pytest-site"


@pytest.mark.usefixtures("dcor_control_config_dir")
def test_check_ckan_ini(monkeypatch, tmp_path):
    site_dir = make_site_config_dir(tmp_path / "site")
    util.set_dcor_control_config("pgsqlpass", "s3cr3t")
    checked = {}

    def check_ckan_ini_option(key, value, autocorrect=False):
        checked[key] = value
        return int(key == "ckan.site_title")

    monkeypatch.setattr(config_ckan, "check_ckan_ini_option",
                        check_ckan_ini_option)
    assert config_ckan.check_ckan_ini(site_dir, autocorrect=True) == 1
    assert checked["ckan.site_title"] == f"Pytest {socket.gethostname()}"


def test_check_ckan_ini_not_managed(monkeypatch):
    monkeypatch.setattr(config_ckan, "get_expected_site_options",
                        lambda path: None)
    assert config_ckan.check_ckan_ini() == 0


def test_update_expected_ckan_options_templates():
    cfg = {"a": "<TEMPLATE:NAME> is <TEMPLATE:AGE>",
           "b": {"c": "<TEMPLATE:NAME>", "d": 1}}
    config_ckan.update_expected_ckan_options_templates(
        cfg, templates={"NAME": [str.upper, ["peter"]],
                        "AGE": [len, ["four"]]})
    assert cfg == {"a": "PETER is 4", "b": {"c": "PETER", "d": 1}}


def test_get_ip():
    assert config_ckan.get_ip().count(".") == 3
