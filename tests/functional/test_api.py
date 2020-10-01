import os
import uuid

from media_management_sdk.api import API


TEST_CLIENT_ID = os.environ.get("MEDIA_MANAGEMENT_API_ID", "media_management_sdk")
TEST_CLIENT_SECRET = os.environ.get("MEDIA_MANAGEMENT_API_SECRET", "only_for_testing")
TEST_BASE_URL = os.environ.get("MEDIA_MANAGEMENT_API_URL", "http://localhost:9000/api")
TEST_USER_ID = 1
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
    title = "My Test Course"
    create_result = api.create_course(
        title=title,
        lti_context_id=generate_ctx_id(),
        lti_tool_consumer_instance_guid="my.institution.edu",
    )
    assert "id" in create_result
    assert create_result["title"] == title
    course_id = create_result["id"]

    # read course
    read_result = api.get_course(course_id)
    assert "id" in read_result
    assert read_result["id"] == course_id

    # update course details
    update_params = dict(
        title=title + " Updated",
        sis_course_id="test123",
        canvas_course_id=100,
        lti_context_title="My Test Context",
        lti_context_label="TCX",
        lti_context_id=create_result[
            "lti_context_id"
        ],  # TODO: why is this required for an update?
        lti_tool_consumer_instance_guid=create_result[
            "lti_tool_consumer_instance_guid"
        ],  # TODO: why is this required for an update?
    )
    update_result = api.update_course(course_id, **update_params)
    update_result_subset = {k: update_result[k] for k in update_params}
    assert update_params == update_result_subset

    # delete the course
    delete_result = api.delete_course(course_id)
    assert delete_result == {}


def test_collection_crud():
    api = API(base_url=TEST_BASE_URL)
    auth_result = api.obtain_token(**TEST_CREDENTIALS)
    api.access_token = auth_result["access_token"]

    # create course
    title = "My Test Course"
    create_result = api.create_course(
        title=title,
        lti_context_id=generate_ctx_id(),
        lti_tool_consumer_instance_guid="our.institution.edu",
    )
    course_id = create_result["id"]

    # create collection
    collection_params = dict(
        title="My Test Collection", description="This is a fascinating collection"
    )
    collection_result = api.create_collection(course_id, **collection_params)
    assert "id" in collection_result
    assert collection_result["title"] == collection_params["title"]
    assert collection_result["description"] == collection_params["description"]
    collection_id = collection_result["id"]

    # update collection
    update_params = dict(
        course_id=course_id,  # TODO: why is this required for an update?
        title=collection_result["title"] + " Updated",
        description=collection_result["description"] + " Updated",
    )
    update_result = api.update_collection(collection_id, **update_params)
    update_result_subset = {k: update_result[k] for k in update_params}
    assert update_params == update_result_subset

    # delete collection
    delete_collection = api.delete_collection(collection_id)
    assert delete_collection == {}

    # delete course
    delete_course = api.delete_course(course_id)
    assert delete_course == {}


def test_upload_image():
    pass
