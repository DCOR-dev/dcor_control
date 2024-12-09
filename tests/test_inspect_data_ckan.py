import os
import pathlib
from unittest import mock

import ckan
import ckan.common
import ckan.model
import ckan.logic
from ckan.tests.helpers import call_action
import ckanext.dcor_schemas.plugin

from dcor_control import inspect
import dcor_shared
from dcor_shared import s3, s3cc
from dcor_shared.testing import make_dataset, synchronous_enqueue_job

import pytest


data_path = pathlib.Path(__file__).parent / "data"


def test_check_orphaned_files_temp(create_with_upload, monkeypatch,
                                   ckan_config, tmpdir):
    """Make sure .rtdc~ files are removed for existing resources"""
    monkeypatch.setitem(ckan_config, 'ckan.storage_path', str(tmpdir))
    monkeypatch.setattr(ckan.lib.uploader,
                        'get_storage_path',
                        lambda: str(tmpdir))

    _, res_dict = make_dataset(
        create_with_upload=create_with_upload,
        resource_path=data_path / "calibration_beads_47.rtdc",
        activate=True,
        authors="Peter Pan")

    path = dcor_shared.get_resource_path(res_dict["id"])
    path_to_delete = path.with_name(path.stem + "_peter.rtdc~")
    path_to_delete.touch()
    assert path_to_delete.exists()
    inspect.check_orphaned_files(assume_yes=True)
    assert not path_to_delete.exists()


@pytest.mark.usefixtures('clean_db', 'with_request_context')
@mock.patch('ckan.plugins.toolkit.enqueue_job',
            side_effect=synchronous_enqueue_job)
def test_check_orphaned_s3_artifacts(enqueue_job_mock, create_with_upload,
                                     monkeypatch, ckan_config, tmpdir):
    monkeypatch.setitem(ckan_config, 'ckan.storage_path', str(tmpdir))
    monkeypatch.setattr(ckan.lib.uploader,
                        'get_storage_path',
                        lambda: str(tmpdir))
    monkeypatch.setattr(
        ckanext.dcor_schemas.plugin,
        'DISABLE_AFTER_DATASET_CREATE_FOR_CONCURRENT_JOB_TESTS',
        True)

    ds_dict, res_dict = make_dataset(
        create_with_upload=create_with_upload,
        resource_path=data_path / "calibration_beads_47.rtdc",
        activate=True,
        private=False,
        authors="Peter Pan")

    rid = res_dict["id"]

    bucket_name, object_name = s3cc.get_s3_bucket_object_for_artifact(rid)

    # Check whether the S3 resource exists
    assert s3.object_exists(bucket_name, object_name)
    # Check that the organization exists
    org_list = ckan.logic.get_action("organization_list")()
    assert ds_dict["organization"]["name"] in org_list

    # Attempt to remove objects from S3, the object should still be there
    # afterward.
    inspect.check_orphaned_s3_artifacts(assume_yes=True,
                                        older_than_days=0)
    assert s3.object_exists(bucket_name, object_name)

    # Delete the entire dataset
    call_action(action_name="package_delete",
                context={'ignore_auth': True, 'user': 'default'},
                id=ds_dict["id"]
                )
    call_action(action_name="dataset_purge",
                context={'ignore_auth': True, 'user': 'default'},
                id=ds_dict["id"]
                )

    # Make sure that the S3 object is still there
    assert s3.object_exists(bucket_name, object_name)

    # Perform a cleanup that does not take into account the new data
    inspect.check_orphaned_s3_artifacts(assume_yes=True,
                                        older_than_days=1)  # [sic]

    # Make sure that the S3 object is still there
    assert s3.object_exists(bucket_name, object_name)

    # Perform the actual cleanup
    inspect.check_orphaned_s3_artifacts(assume_yes=True,
                                        older_than_days=0)
    assert not s3.object_exists(bucket_name, object_name)


def test_get_dcor_site_config_dir():
    cur_dir = os.environ.get("DCOR_SITE_CONFIG_DIR")
    try:
        os.environ["DCOR_SITE_CONFIG_DIR"] = "/tmp/test"
        assert str(inspect.get_dcor_site_config_dir()) == "/tmp/test"
    except BaseException:
        raise
    finally:
        # cleanup
        if cur_dir is not None:
            os.environ["DCOR_SITE_CONFIG_DIR"] = cur_dir
        else:
            os.environ.pop("DCOR_SITE_CONFIG_DIR")
