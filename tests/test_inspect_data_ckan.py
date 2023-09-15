import pathlib

import ckan
import ckan.common
import ckan.model
import ckan.tests.factories as factories
import dcor_shared

from dcor_control import inspect

from helper_methods import make_dataset


data_path = pathlib.Path(__file__).parent / "data"


def test_check_orphaned_files(create_with_upload, monkeypatch, ckan_config,
                              tmpdir):
    """Make sure .rtdc~ files are removed for existing resources"""
    monkeypatch.setitem(ckan_config, 'ckan.storage_path', str(tmpdir))
    monkeypatch.setattr(ckan.lib.uploader,
                        'get_storage_path',
                        lambda: str(tmpdir))

    user = factories.User()

    user_obj = ckan.model.User.by_name(user["name"])
    monkeypatch.setattr(ckan.common,
                        'current_user',
                        user_obj)

    owner_org = factories.Organization(users=[{
        'name': user['id'],
        'capacity': 'admin'
    }])
    # Note: `call_action` bypasses authorization!
    # create 1st dataset
    create_context1 = {'ignore_auth': False,
                       'user': user['name'], 'api_version': 3}

    _, res = make_dataset(create_context1, owner_org,
                          create_with_upload=create_with_upload,
                          activate=True,
                          authors="Peter Pan")

    path = dcor_shared.get_resource_path(res["id"])
    path_to_delete = path.with_name(path.stem + "_peter.rtdc~")
    path_to_delete.touch()
    assert path_to_delete.exists()
    inspect.check_orphaned_files(assume_yes=True)
    assert not path_to_delete.exists()
