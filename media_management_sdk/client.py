from typing import Optional

from media_management_sdk.api import API
from media_management_sdk.exceptions import ApiError


class Client(object):
    """
    Client is a wrapper for interacting with the API.
    """

    def __init__(self, client_id: str, client_secret: str, base_url: str):
        if client_id is None or client_secret is None:
            raise ValueError("Missing client credentials")
        if base_url is None:
            raise ValueError("Missing base URL to use for API requests")

        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.api = API(base_url=base_url)

    def authenticate(
        self,
        user_id: str,
        course_id: Optional[int] = None,
        course_permission: Optional[str] = None,
    ):
        """
        Authenticate with the API by supplying client credentials and obtaining
        a token tied to the user.
        """
        if not user_id:
            raise ValueError("User ID is required to authenticate")
        response = self.api.obtain_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_id=user_id,
            course_id=course_id,
            course_permission=course_permission,
        )
        self.api.access_token = response["access_token"]

    def find_or_create_course(
        self,
        lti_context_id: str,
        lti_tool_consumer_instance_guid: str,
        title: str = "",
        lti_context_title: Optional[str] = None,
        lti_context_label: Optional[str] = None,
        sis_course_id: Optional[str] = None,
        canvas_course_id: Optional[int] = None,
    ):
        """
        Helper method to find or create a course.
        """
        courses = self.api.list_courses(
            lti_context_id=lti_context_id,
            lti_tool_consumer_instance_guid=lti_tool_consumer_instance_guid,
        )
        if len(courses) > 1:
            raise ApiError("Multiple courses found")
        elif len(courses) == 1:
            return courses[0]

        return self.api.create_course(
            title=title,
            lti_context_id=lti_context_id,
            lti_tool_consumer_instance_guid=lti_tool_consumer_instance_guid,
            lti_context_title=lti_context_title,
            lti_context_label=lti_context_label,
            sis_course_id=sis_course_id,
            canvas_course_id=canvas_course_id,
        )
