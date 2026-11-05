import os
import subprocess as sp
import types
import uuid

import pytest

import numpy as np
from dcor_control import update


@pytest.mark.parametrize("name,ckan_version,version",
                         [
                             # latest version always returns None
                             ("ckanext-dc_log_view", None, None),
                             ("ckanext-dc_log_view", "2.9.0", "0.2.2"),
                             # CKAN 2.11.7 is the latest version listed
                             ("ckanext-dcor_theme", "2.11.7", None),
                             # releases for CKAN 2.11.7 also work with
                             # CKAN 2.11.5 and 2.11.6
                             ("ckanext-dcor_theme", "2.11.6", "1.1.5"),
                             ("ckanext-dcor_schemas", "2.11.5", "1.2.0"),
                             ("ckanext-dc_serve", "2.11.5", "1.0.10"),
                             # CKAN 2.11.3 keeps the previous releases
                             ("ckanext-dcor_theme", "2.11.3", "1.1.4"),
                         ])
def test_get_max_compatible_version(name, ckan_version, version):
    assert update.get_max_compatible_version(
        name, ckan_version=ckan_version) == version


def test_get_max_compatible_version_invalid():
    with pytest.raises(IndexError, match="Could not find current CKAN versio"):
        update.get_max_compatible_version(name="ckanext-dc_log_view",
                                          ckan_version="1.2")


@pytest.mark.parametrize("name,version",
                         [
                             ("numpy", np.__version__),
                             (str(uuid.uuid4()).replace("-", ""), None),
                         ])
def test_get_package_version(name, version):
    assert update.get_package_version(name) == version


def test_parse_compatible_versions():
    data = update.parse_compatible_versions()
    # make sure this line exists
    # 2.10.1 0.3.2 0.14.0 0.8.1 0.13.7 0.18.9 0.7.6 0.9.3 0.5.5
    dict_exp = {
        'ckan': '2.10.1',
        'ckanext-dc_log_view': '0.3.2',
        'ckanext-dc_serve': '0.14.0',
        'ckanext-dc_view': '0.8.1',
        'ckanext-dcor_depot': '0.13.7',
        'ckanext-dcor_schemas': '0.18.9',
        'ckanext-dcor_theme': '0.7.6',
        'dcor_control': '0.9.3',
        'dcor_shared': '0.5.5',
    }
    assert dict_exp in data


@pytest.mark.parametrize("va,vb,result", [
    # Truly greater
    ("2", "1", True),
    ("2.1", "2.0", True),
    ("2.10.1", "2.10.0", True),
    ("2.10.1.b", "2.10.1.a", True),
    ("2.10.1.bommel3", "2.10.1.bommel2", True),
    ("2.10.1.bommel3 ", "2.10.1.bommel2", True),
    # Equal
    ("1", "1", False),
    ("1.1", "1.1", False),
    ("Peter", "Peter", False),
    # Smaller
    ("2", "3", False),
    ("2.1", "2.2", False),
    ("2.10.1", "2.10.2", False),
    ("2.10.1.b", "2.10.1.c", False),
    ("2.10.1.bommel1", "2.10.1.bommel2", False),
])
def test_version_greater(va, vb, result):
    assert update.version_greater(va, vb) == result


@pytest.mark.parametrize("va,vb,result", [
    # Truly greater
    ("2", "1", True),
    ("2.1", "2.0", True),
    ("2.10.1", "2.10.0", True),
    ("2.10.1.b", "2.10.1.a", True),
    ("2.10.1.bommel3", "2.10.1.bommel2", True),
    # Equal
    ("1", "1", True),
    ("1.1", "1.1", True),
    ("Peter", "Peter", True),
    ("Peter", "Peter ", True),
    # Smaller
    ("2", "3", False),
    ("2 ", "3 ", False),
    ("2.1", "2.2", False),
    ("2.10.1", "2.10.2", False),
    ("2.10.1.b", "2.10.1.c", False),
    ("2.10.1.bommel1", "2.10.1.bommel2", False),
])
def test_version_greater_equal(va, vb, result):
    assert update.version_greater_equal(va, vb) == result


def test_get_package_version_git(tmp_path):
    repo = tmp_path / "ckanext-peter"
    repo.mkdir()
    git = f"git -C {repo} -c user.name=pytest -c user.email=pytest@localhost"
    sp.check_output(f"{git} init -q", shell=True)
    sp.check_output(f"{git} commit -q --allow-empty -m init", shell=True)
    sp.check_output(f"{git} tag -a 1.2.3 -m 1.2.3", shell=True)
    # the "." in the name is replaced with "-"
    assert update.get_package_version_git("ckanext.peter", tmp_path) \
        == "1.2.3"
    with pytest.raises(ValueError, match="Could not find ckanext.hans"):
        update.get_package_version_git("ckanext.hans", tmp_path)


@pytest.fixture
def mock_update_package(monkeypatch, tmp_path):
    """Pretend to be a package installed in `tmp_path / "pkg"`"""
    calls = []
    pkg_dir = tmp_path / "pkg" / "dcor_peter"
    pkg_dir.mkdir(parents=True)
    module = types.SimpleNamespace(__file__=str(pkg_dir / "__init__.py"))
    monkeypatch.setattr(update.importlib, "import_module",
                        lambda name: module)
    monkeypatch.setattr(update.sp, "check_output",
                        lambda cmd, shell: calls.append(cmd))
    versions = iter(["1.0.0", "1.1.0"])
    monkeypatch.setattr(update, "get_package_version",
                        lambda name: next(versions))
    monkeypatch.setattr(update, "get_pip_executable_path", lambda: "pip")
    return calls, tmp_path / "pkg"


@pytest.mark.parametrize("req_version,pin", [(None, ""), ("1.0.5", "==1.0.5")])
def test_update_package_pip(monkeypatch, capsys, mock_update_package,
                            req_version, pin):
    calls, _ = mock_update_package
    monkeypatch.setattr(update, "get_max_compatible_version",
                        lambda name: req_version)
    assert update.update_package("dcor_peter") == "1.1.0"
    assert calls == [f"pip install --upgrade dcor_peter{pin}"]
    assert "updated dcor_peter from 1.0.0 to 1.1.0" in capsys.readouterr().out


def test_update_package_git(mock_update_package):
    calls, pkg_root = mock_update_package
    (pkg_root / ".git").mkdir()
    wd = os.getcwd()
    assert update.update_package("dcor_peter") == "1.1.0"
    assert calls == ["git pull", "pip install -e ."]
    assert os.getcwd() == wd


def test_update_package_git_pull_fails(monkeypatch, mock_update_package):
    calls, pkg_root = mock_update_package
    (pkg_root / ".git").mkdir()

    def check_output(cmd, shell):
        calls.append(cmd)
        raise sp.CalledProcessError(1, cmd)

    monkeypatch.setattr(update.sp, "check_output", check_output)
    update.update_package("dcor_peter")
    # pip is not called when git pull failed
    assert calls == ["git pull"]
