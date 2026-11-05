import pytest


@pytest.fixture
def dcor_control_config_dir(monkeypatch, tmp_path):
    """Store dcor_control configuration keys in a temporary directory"""
    cpath = tmp_path / "dcor_control_config"
    monkeypatch.setattr("appdirs.user_config_dir", lambda name: str(cpath))
    return cpath
