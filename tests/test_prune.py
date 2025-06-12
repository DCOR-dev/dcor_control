import pathlib
from unittest import mock

import ckan
import ckan.common
import ckan.model
import ckan.logic

from ckan.tests.helpers import call_action

from dcor_control import inspect
from dcor_shared import s3, s3cc
from dcor_shared.testing import make_dataset_via_s3, synchronous_enqueue_job

import pytest


data_path = pathlib.Path(__file__).parent / "data"


@pytest.mark.ckan_config('ckan.plugins', 'dcor_schemas')
@pytest.mark.usefixtures('clean_db', 'with_request_context')
@mock.patch('ckan.plugins.toolkit.enqueue_job',
            side_effect=synchronous_enqueue_job)
def test_check_orphaned_s3_artifacts(enqueue_job_mock):
    ds_dict, res_dict = make_dataset_via_s3(
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
