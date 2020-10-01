import os
import os.path
import uuid

from media_management_sdk.api import API

TEST_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")

TEST_CLIENT_ID = os.environ.get("MEDIA_MANAGEMENT_API_ID", "media_management_sdk")
TEST_CLIENT_SECRET = os.environ.get(
    "MEDIA_MANAGEMENT_API_SECRET", "only_for_test"
)
TEST_BASE_URL = os.environ.get(
    "MEDIA_MANAGEMENT_API_URL", "https://localhost:9000/api"
)
TEST_USER_ID = os.environ.get("MEDIA_MANAGEMENT_API_USER_ID", "123456789")

TEST_CREDENTIALS = dict(
    client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET, user_id=TEST_USER_ID
)


def generate_ctx_id():
    """ Returns a unique LTI context ID """
    return "test:" + str(uuid.uuid1())


def test_obtain_token():
    api = API(base_url=TEST_BASE_URL)
    auth_result = api.obtain_token(**TEST_CREDENTIALS)
    assert "access_token" in auth_result
    assert len(auth_result["access_token"]) > 0
    assert "user_id" in auth_result
    assert auth_result["user_id"] == TEST_CREDENTIALS["user_id"]
    assert "expires" in auth_result


def test_course_crud():
    api = API(base_url=TEST_BASE_URL)

    # obtain token
    auth_result = api.obtain_token(**TEST_CREDENTIALS)
    api.access_token = auth_result["access_token"]

    # create course
    title = "SDK Test"
    course_created = api.create_course(
        title=title,
        lti_context_id=generate_ctx_id(),
        lti_tool_consumer_instance_guid="test.institution.edu",
    )
    assert "id" in course_created
    assert course_created["title"] == title
    course_id = course_created["id"]

    # read course
    course_read = api.get_course(course_id)
    assert "id" in course_read
    assert course_read["id"] == course_id

    # update course details
    update_params = dict(
        title=title + " Updated",
        sis_course_id="test123",
        canvas_course_id=100,
        lti_context_title="My Test Context",
        lti_context_label="TCX",
        lti_context_id=course_created[
            "lti_context_id"
        ],  # TODO: why is this required for an update?
        lti_tool_consumer_instance_guid=course_created[
            "lti_tool_consumer_instance_guid"
        ],  # TODO: why is this required for an update?
    )
    course_updated = api.update_course(course_id, **update_params)
    course_updated_subset = {k: course_updated[k] for k in update_params}
    assert update_params == course_updated_subset

    # delete the course
    course_deleted = api.delete_course(course_id)
    assert course_deleted == {}


def test_collection_crud():
    api = API(base_url=TEST_BASE_URL)
    auth_result = api.obtain_token(**TEST_CREDENTIALS)
    api.access_token = auth_result["access_token"]

    # create course
    title = "SDK Test"
    course_created = api.create_course(
        title=title,
        lti_context_id=generate_ctx_id(),
        lti_tool_consumer_instance_guid="test.institution.edu",
    )
    course_id = course_created["id"]

    # create collection
    collection_params = dict(
        title="SDK Test",
        description="This is a fascinating collection",
    )
    collection_created = api.create_collection(course_id, **collection_params)
    assert "id" in collection_created
    assert collection_created["title"] == collection_params["title"]
    assert collection_created["description"] == collection_params["description"]
    collection_id = collection_created["id"]

    # update collection
    update_params = dict(
        course_id=course_id,  # TODO: why is this required for an update?
        title=collection_created["title"] + " Updated",
        description=collection_created["description"] + " Updated",
    )
    collection_updated = api.update_collection(collection_id, **update_params)
    collection_updated_subset = {k: collection_updated[k] for k in update_params}
    assert update_params == collection_updated_subset

    # delete collection
    collection_deleted = api.delete_collection(collection_id)
    assert collection_deleted == {}

    # delete course
    course_deleted = api.delete_course(course_id)
    assert course_deleted == {}


def test_image_crud():
    api = API(base_url=TEST_BASE_URL)
    auth_result = api.obtain_token(**TEST_CREDENTIALS)
    api.access_token = auth_result["access_token"]

    # create course
    course_created = api.create_course(
        title="SDK Test",
        lti_context_id=generate_ctx_id(),
        lti_tool_consumer_instance_guid="test.institution.edu",
    )
    course_id = course_created["id"]

    # upload a single image to the course
    image_id = None
    file_name = "16x16-ff00ff7f.png"
    content_type = "image/png"
    with open(os.path.join(TEST_IMAGES_DIR, file_name), "rb") as upload_file:
        image_uploaded = api.upload_image(
            course_id,
            upload_file=upload_file,
            file_name=file_name,
            content_type=content_type,
            title="Color Block Image",
        )
        assert len(image_uploaded) == 1, "list returned with the uploaded image"
        assert "id" in image_uploaded[0], "the image has an id"
        image_id = image_uploaded[0]["id"]

    # get image details
    image_read = api.get_image(image_id)
    assert image_read["id"] == image_id

    # update image details
    update_params = dict(
        course_id=course_id,
        title=image_read["title"] + " Updated",
        description="Color block is amazing!",
        metadata=dict(Creator="SDK", Audience="Test", Date="2000"),
    )
    image_updated = api.update_image(image_id, **update_params)
    assert image_updated["id"] == image_id
    assert image_updated["title"] == update_params["title"]

    # delete image
    image_deleted = api.delete_image(image_id)
    assert image_deleted == {}

    # delete course
    api.delete_course(course_id)


def test_upload_multiple_images_and_add_to_collection():
    api = API(base_url=TEST_BASE_URL)
    auth_result = api.obtain_token(**TEST_CREDENTIALS)
    api.access_token = auth_result["access_token"]

    # create course
    course_created = api.create_course(
        title="SDK Test",
        lti_context_id=generate_ctx_id(),
        lti_tool_consumer_instance_guid="test.institution.edu",
    )
    course_id = course_created["id"]

    # upload multiple images to the course
    image_ids = []
    content_type = "image/png"
    upload_files = [
        (file_name, open(os.path.join(TEST_IMAGES_DIR, file_name), "rb"), content_type)
        for file_name in (
            "16x16-ff00ff7f.png",
            "32x32-faaa1aff.png",
            "64x64-ff0000c1.png",
        )
    ]
    try:
        images_uploaded = api.upload_images(
            course_id,
            upload_files=upload_files,
            title="Color Block",
        )
        assert len(images_uploaded) == 3, "list returned with the uploaded image"
        image_ids = [image["id"] for image in images_uploaded]
    finally:
        for (file_name, fp, content_type) in upload_files:
            fp.close()

    # create collection
    collection_created = api.create_collection(
        course_id, title="SDK Test", description="Just a test"
    )
    collection_id = collection_created["id"]

    # add images to collection
    update_params = dict(
        course_id=course_id,
        title=collection_created["title"],
        course_image_ids=image_ids,
    )
    collection_updated = api.update_collection(collection_id, **update_params)
    assert collection_updated["course_image_ids"] == image_ids

    # delete course
    api.delete_course(course_id)
