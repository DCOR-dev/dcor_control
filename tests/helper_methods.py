import pathlib

import ckan.tests.helpers as helpers


data_path = pathlib.Path(__file__).parent / "data"


def make_dataset(create_context, owner_org, create_with_upload=None,
                 activate=False, **kwargs):
    if "title" not in kwargs:
        kwargs["title"] = "test-dataset"
    if "authors" not in kwargs:
        kwargs["authors"] = "Peter Pan"
    if "license_id" not in kwargs:
        kwargs["license_id"] = "CC-BY-4.0"
    assert "state" not in kwargs, "must not be set"
    assert "owner_org" not in kwargs, "must not be set"
    # create a dataset
    ds = helpers.call_action("package_create", create_context,
                             owner_org=owner_org["name"],
                             state="draft",
                             **kwargs
                             )

    if create_with_upload is not None:
        rs = make_resource(create_with_upload, create_context, ds["id"])

    if activate:
        helpers.call_action("package_patch", create_context,
                            id=ds["id"],
                            state="active")

    dataset = helpers.call_action("package_show", id=ds["id"])

    if create_with_upload is not None:
        return dataset, rs
    else:
        return dataset


def make_resource(create_with_upload, create_context, dataset_id):
    content = (data_path / "calibration_beads_47.rtdc").read_bytes()
    rs = create_with_upload(
        data=content,
        filename='test.rtdc',
        context=create_context,
        package_id=dataset_id,
        url="upload",
    )
    resource = helpers.call_action("resource_show", id=rs["id"])
    return resource
