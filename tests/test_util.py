import sys

import pytest

from dcor_control import util


def test_dcor_control_config(dcor_control_config_dir):
    assert util.set_dcor_control_config("email", "peter@example.com") \
        == "peter@example.com"
    assert util.get_dcor_control_config("email") == "peter@example.com"
    assert (dcor_control_config_dir / "email").stat().st_mode & 0o777 \
        == 0o600


@pytest.mark.usefixtures("dcor_control_config_dir")
def test_dcor_control_config_not_interactive():
    assert util.get_dcor_control_config("email", interactive=False) is None


def test_dcor_control_config_prompt(monkeypatch, capsys,
                                    dcor_control_config_dir):
    monkeypatch.setattr("builtins.input", lambda prompt: "hans@example.com")
    data = util.get_dcor_control_config("email",
                                        custom_message="Hello Hans")
    assert data == "hans@example.com"
    assert "Hello Hans" in capsys.readouterr().out
    # stored for later use
    assert (dcor_control_config_dir / "email").read_text() \
        == "hans@example.com"


def test_get_module_installation_path():
    assert util.get_module_installation_path("dcor_control").endswith(
        "dcor_control")
    assert util.get_module_installation_path(
        "dcor_control_nonexistent_module") == "/tmp/unknown"


def test_get_pip_executable_path(monkeypatch, tmp_path):
    (tmp_path / "pip").touch()
    monkeypatch.setattr(sys, "path", [str(tmp_path / "nope"), str(tmp_path)])
    assert util.get_pip_executable_path() == tmp_path / "pip"


def test_get_pip_executable_path_not_found(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "path", [str(tmp_path)])
    with pytest.raises(ValueError, match="Could not find `pip`"):
        util.get_pip_executable_path()
