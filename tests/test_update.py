import pytest
import uuid

import numpy as np
from dcor_control import update


@pytest.mark.parametrize("name,ckan_version,version",
                         [
                             # latest version always returns None
                             ("ckanext-dc_log_view", None, None),
                             ("ckanext-dc_log_view", "2.9.0", "0.2.2"),
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
