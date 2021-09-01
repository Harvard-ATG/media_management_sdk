from unittest.mock import Mock, PropertyMock, patch

import pytest

from media_management_sdk.api import API, DEFAULT_TIMEOUT
from media_management_sdk.exceptions import (
    ApiError,
    ApiForbiddenError,
    ApiNotFoundError,
    ApiHTTPError,
)
from media_management_sdk.jwt import create_jwt

TEST_BASE_URL = "http://localhost:8000/api"
TEST_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}
TEST_CLIENT_ID = "myapp"
TEST_CLIENT_SECRET = "07c91feb29b393e9418416aef05b433d9de7f638"
TEST_USER_ID = "x123456x"


@pytest.fixture
def courses_fixture():
    names = ("John Leverett", "Edward Wigglesworth", "Samuel Webber", "Josiah Quincy")
    courses = [
        dict(
            id=i,
            title=f"{name}'s demo course",
            canvas_course_id=i + 1000,
            sis_course_id="demo-" + name.replace(" ", ""),
            lti_context_id=f"2a8b213eb085b7866a9{i}",
            lti_tool_consumer_instance_guid="1ea41637.myinstitution.edu",
        )
        for i, name in enumerate(names, start=1)
    ]
    return courses


@pytest.mark.parametrize("http_method", ["get", "post", "put", "delete"])
@pytest.mark.parametrize("status_code", [200, 201])
def test_do_request_with_method(http_method, status_code):
    url = f"{TEST_BASE_URL}/test/123"
    expected_response = {"id": "100"}

    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.json = Mock(return_value=expected_response)

    with patch(f"requests.{http_method}", return_value=mock_resp) as mock_method:
        actual_response = API()._do_request(method=http_method, url=url)
        mock_method.assert_called_once_with(url, timeout=DEFAULT_TIMEOUT)
        assert actual_response == expected_response


@pytest.mark.parametrize("http_method", ["get", "post", "put", "delete"])
@pytest.mark.parametrize(
    "status_code,error_class",
    [
        (400, ApiHTTPError),
        (403, ApiForbiddenError),
        (404, ApiNotFoundError),
        (408, ApiHTTPError),
        (500, ApiHTTPError),
    ],
)
def test_do_request_raises_exception_for_status(http_method, status_code, error_class):
    expected_url = f"{TEST_BASE_URL}/test/123"
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = Mock(side_effect=error_class)
    mock_resp.json = Mock(return_value=None)
    with patch(f"requests.{http_method}", return_value=mock_resp) as mock_method:
        with pytest.raises(error_class):
            API()._do_request(method=http_method, url=expected_url)



def test_authorize_user(courses_fixture):
    course = courses_fixture[0]
    token_data = {
        "client_id": TEST_CLIENT_ID,
        "client_secret": TEST_CLIENT_SECRET,
        "user_id": TEST_USER_ID,
        "course_id": course["id"],
        "course_permission": "write",
    }
    access_token = create_jwt(**token_data)
    headers = dict(**TEST_HEADERS, Authorization=f"Bearer {access_token}")

    api = API(base_url=TEST_BASE_URL, access_token=access_token)
    api._do_request = Mock(return_value={"success": True})
    actual_response = api.authorize_user()
    api._do_request.assert_called_with(
        method="post",
        url=f"{TEST_BASE_URL}/auth/authorize-user",
        headers=headers,
    )
    assert actual_response["success"] is True


def test_list_courses_filtered_by_lti_params(courses_fixture):
    course = courses_fixture[0]

    access_token = "token123"
    headers = dict(**TEST_HEADERS, Authorization=f"Bearer {access_token}")
    params = dict(
        lti_context_id=course["lti_context_id"],
        lti_tool_consumer_instance_guid=course["lti_tool_consumer_instance_guid"],
        canvas_course_id=None,
        sis_course_id=None,
        title=None,
    )

    api = API(base_url=TEST_BASE_URL, access_token=access_token)
    api._do_request = Mock(return_value=[course])
    actual_response = api.list_courses(**params)
    api._do_request.assert_called_with(
        method="get", url=f"{TEST_BASE_URL}/courses", headers=headers, params=params
    )
    assert actual_response == [course]


def test_api_implements_required_methods():
    methods = (
        "authorize_user",
        "list_courses",
        "search_courses",
        "get_course",
        "create_course",
        "update_course",
        "delete_course",
        "copy_course",
        "list_collections",
        "get_collection",
        "get_collection_images",
        "create_collection",
        "update_collection",
        "delete_collection",
        "upload_image",
        "upload_images",
        "update_image",
        "get_image",
        "delete_image",
    )
    api = API()
    for method in methods:
        assert hasattr(api, method)
        assert callable(getattr(api, method))
