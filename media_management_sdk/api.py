import logging
import json
import requests
from typing import Any, Dict, List, IO, Optional, Tuple, Union

from media_management_sdk.exceptions import (
    ApiError,
    ApiHTTPError,
    ApiBadRequest,
    ApiForbiddenError,
    ApiNotFoundError,
)

logger = logging.getLogger(__name__)

GET, POST, PUT, DELETE = ("get", "post", "put", "delete")
DEFAULT_TIMEOUT = 30


class API(object):
    """
    This class includes methods for interacting with REST API endpoints.
    """

    def __init__(
        self, base_url: Optional[str] = None, access_token: Optional[str] = None
    ) -> None:
        """API constructor.

        Args:
            base_url: The base URL that will prefix all
                endpoint requests. Defaults to None.
            access_token: The access token to use for requests
                that require authorization. Defaults to None.
        """
        self.base_url = base_url
        self.access_token = access_token

    @property
    def headers(self) -> Dict[str, str]:
        """Get the HTTP headers needed for API requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.access_token is not None:
            headers["Authorization"] = f"Token {self.access_token}"
        return headers

    def _do_request(self, method: str, url: str, **kwargs) -> Union[List, Dict]:
        """Performs the HTTP request, delegating to the requests library for
        the actual request itself.

        This method centralizes exception handling and logging as
        well as defaults for all requests.

        Args:
            method: A valid HTTP method (e.g. get, post, put, delete).
            url: The endpoint URL.
            **kwargs: Arbitrary keyword arguments. These are passed directly
                to the underlying request method (e.g. requests.get).

        Raises:
            ValueError: If the request method is invalid.
            ApiForbiddenError: If HTTP 403 response.
            ApiNotFoundError: If HTTP 404 response.
            ApiHTTPError: If any other 4xx or 5xx response
            ApiError: If any other request exception

        Returns:
            Response data.
        """
        request_callable = getattr(requests, method)
        if not request_callable:
            raise ValueError(f"Invalid request method: {method}")
        if not url:
            raise ValueError("URL must be provided for the request")

        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)

        # Log the request, omitting a few items such as:
        # - headers, because they may contain auth credentials
        # - file objects, because they may contain binary data
        log_kwargs = json.dumps(
            {k: kwargs[k] for k in kwargs if k != "headers" and k != "files"}
        )
        logger.info(f"API request [{method} {url}] {log_kwargs}")

        try:
            r = request_callable(url, **kwargs)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.exception("HTTP error")
            status_code = e.response.status_code
            detail = e.response.text  ## TODO: this might be json
            if status_code == 400:
                raise ApiBadRequest(detail)
            if status_code == 403:
                raise ApiForbiddenError(detail)
            elif status_code == 404:
                raise ApiNotFoundError(detail)
            else:
                raise ApiHTTPError(f"HTTP error status code: {status_code}")
        except requests.exceptions.RequestException as e:
            logger.exception("Request error")
            raise ApiError("Request exception: " + str(e))

        try:
            data = r.json()
        except ValueError as e:
            if r.status_code == 204:
                data = {}
            else:
                logger.exception("No JSON object could be decoded")
                raise ApiError("No JSON object could be decoded")

        return data

    def obtain_token(
        self,
        client_id: str,
        client_secret: str,
        user_id: str,
        course_id: Optional[int] = None,
        course_permission: Optional[str] = None,
    ):
        """
        Obtains a temporary access token.

        Args:
            client_id: Identifies the client application. Obtained from API /admin.
            client_secret: Identifies the client application. Obtained from API /admin.
            user_id: The SIS User ID.
            course_id: The PK of the course object that exists in the API. Used to
                grant the user access to the course if they didn't create it.
            course_permission: One of "read" or "write", defaults to "read". Used
                together with the course_id parameter to grant admin access to the course.

        Returns:
            dict: Response containing the "access_token" required for making authenticated requests.

        Raises:
            ValueError: If course_permission is invalid.
            ApiError: Raised on 4XX or 5XX error response.
        """
        valid_permissions = ("read", "write")
        if course_permission and course_permission not in valid_permissions:
            raise ValueError(
                f"Invalid course_permission parameter. Must be one of: {valid_permissions}"
            )

        url = f"{self.base_url}/auth/obtain-token"
        params = dict(client_id=client_id, client_secret=client_secret, user_id=user_id)
        if course_id:
            params["course_id"] = str(course_id)
        if course_id and course_permission:
            params["course_permission"] = course_permission
        return self._do_request(method=POST, url=url, headers=self.headers, json=params)

    def list_courses(
        self,
        lti_context_id: Optional[str] = None,
        lti_tool_consumer_instance_guid: Optional[str] = None,
        canvas_course_id: Optional[int] = None,
        sis_course_id: Optional[str] = None,
        title: Optional[str] = None,
    ):
        """List courses.

        Filter the list of courses by providing a value for one or more of the course attributes.
        In an LTI context, the *lti_context_id* and *lti_tool_consumer_instance_guid*
        are commonly used to find a particular course.

        Args:
            lti_context_id: LTI context ID. Defaults to None.
            lti_tool_consumer_instance_guid: LTI consumer instance GUID. Defaults to None.
            canvas_course_id: Canvas course ID. Defaults to None.
            sis_course_id: SIS course ID. Defaults to None.
            title: Course title. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses"
        params = dict(
            lti_context_id=lti_context_id,
            lti_tool_consumer_instance_guid=lti_tool_consumer_instance_guid,
            canvas_course_id=canvas_course_id,
            sis_course_id=sis_course_id,
            title=title,
        )
        return self._do_request(
            method=GET, url=url, headers=self.headers, params=params
        )

    def search_courses(self, text: str = ""):
        """Search courses.

        Args:
            text: Search text.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/search"
        params = dict(q=text)
        return self._do_request(
            method=GET, url=url, headers=self.headers, params=params
        )

    def get_course(self, course_id: int):
        """Get a course.

        Args:
            course_id: Course ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def create_course(
        self,
        title: str,
        lti_context_id: str,
        lti_tool_consumer_instance_guid: str,
        lti_context_title: Optional[str] = None,
        lti_context_label: Optional[str] = None,
        sis_course_id: Optional[str] = None,
        canvas_course_id: Optional[int] = None,
    ):
        """Create a course.

        Args:
            title: Course title.
            lti_context_id: LTI context ID.
            lti_tool_consumer_instance_guid: Tool consumer instance GUID.
            lti_context_title: LTI context title. Defaults to None.
            lti_context_label: LTI context label. Defaults to None.
            sis_course_id: SIS course ID. Defaults to None.
            canvas_course_id: Canvas course ID. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses"
        params = dict(
            lti_context_id=lti_context_id,
            lti_tool_consumer_instance_guid=lti_tool_consumer_instance_guid,
            lti_context_title=lti_context_title,
            lti_context_label=lti_context_label,
            title=title,
            sis_course_id=sis_course_id,
            canvas_course_id=canvas_course_id,
        )
        params = {k: v for k, v in params.items() if v is not None}
        return self._do_request(method=POST, url=url, headers=self.headers, json=params)

    def update_course(
        self,
        course_id: int,
        title: str = None,
        sis_course_id: Optional[str] = None,
        canvas_course_id: Optional[int] = None,
        lti_context_id: Optional[str] = None,
        lti_tool_consumer_instance_guid: Optional[str] = None,
        lti_tool_consumer_instance_name: Optional[str] = None,
        lti_context_title: Optional[str] = None,
        lti_context_label: Optional[str] = None,
    ):
        """Create a course.

        Args:
            course_id: Course ID.
            title: Course title.
            sis_course_id: SIS course ID. Defaults to None.
            canvas_course_id: Canvas course ID. Defaults to None.
            lti_context_id: LTI context ID. Defaults to None.
            lti_tool_consumer_instance_guid: Tool consumer instance GUID. Defaults to None.
            lti_tool_consumer_instance_name: Tool consumer instance Name. Defaults to None.
            lti_context_title: LTI context title. Defaults to None.
            lti_context_label: LTI context label. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}"
        params = dict(
            lti_context_id=lti_context_id,
            lti_tool_consumer_instance_guid=lti_tool_consumer_instance_guid,
            lti_tool_consumer_instance_name=lti_tool_consumer_instance_name,
            lti_context_title=lti_context_title,
            lti_context_label=lti_context_label,
            title=title,
            sis_course_id=sis_course_id,
            canvas_course_id=canvas_course_id,
        )
        params = {k: v for k, v in params.items() if v is not None}
        return self._do_request(method=PUT, url=url, headers=self.headers, json=params)

    def delete_course(self, course_id: int):
        """Deletes a course.

        Args:
            course_id: Course ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}"
        return self._do_request(method=DELETE, url=url, headers=self.headers)

    def copy_course(self, src_course_id: int, dest_course_id: int):
        """Copy a course and all of its resources.

        Note that the destination course must already exist.

        Args:
            src_course_id: Course that is the source of the copy.
            dest_course_id: Course that is the destination of the copy.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{dest_course_id}/course_copy"
        params = dict(source_id=src_course_id)
        return self._do_request(method=POST, url=url, headers=self.headers, json=params)

    def list_collections(self, course_id: int):
        """Lists collections in a course.

        Args:
            course_id: Course ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}/collections"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def get_collection(self, collection_id: int):
        """Get collection details.

        Args:
            collection_id: Collection ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/collections/{collection_id}"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def get_collection_images(self, collection_id: int):
        """Get collection images.

        Args:
            collection_id: Collection ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/collections/{collection_id}/images"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def create_collection(
        self, course_id: int, title: str, description: Optional[str] = None
    ):
        """Create a collection.

        Args:
            course_id: Course ID.
            title: Collection title.
            description: Collection description. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}/collections"
        params = dict(title=title, description=description, course_id=course_id)
        return self._do_request(method=POST, url=url, headers=self.headers, json=params)

    def update_collection(
        self,
        collection_id: int,
        course_id: int,
        title: str,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
        course_image_ids: Optional[List[int]] = None,
    ):
        """Update a collection.

        Args:
            collection_id: Collection ID.
            course_id: Course ID.
            title: Collection title.
            description: Collection description. Defaults to None.
            sort_order: Collection sort order. Defaults to None.
            course_image_ids: The list of images that should be part of this collection,
                which should reference images from the course image library (course image IDs). Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/collections/{collection_id}"
        params = dict(
            course_id=course_id,
            title=title,
            description=description,
            sort_order=sort_order,
            course_image_ids=course_image_ids,
        )
        params = {k: v for k, v in params.items() if v is not None}
        return self._do_request(method=PUT, url=url, headers=self.headers, json=params)

    def delete_collection(self, collection_id: int):
        """Deletes a collection.

        Args:
            collection_id: Collection ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/collections/{collection_id}"
        return self._do_request(method=DELETE, url=url, headers=self.headers)

    def upload_image(
        self,
        course_id: int,
        upload_file: IO,
        file_name: str,
        content_type: str,
        title: str,
    ):
        """Upload a single image to the course.

        Args:
            course_id: Course ID.
            upload_file: File object (e.g. implements read method).
            file_name: The name of the file.
            content_type: The MIME type for the file.
            title: Title to use for the file. Note that if
                not specified, the original file name will be used. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        return self.upload_images(
            course_id, [(file_name, upload_file, content_type)], title=title
        )

    def upload_images(
        self,
        course_id: int,
        upload_files: List[Tuple[str, IO, str]],
        title: Optional[str] = None,
    ):
        """Upload images to the course.

        Args:
            course_id: Course ID.
            upload_files: List of file tuples: (filename, file, content_type).
            title: Title to use for the file or list of files. Note that if
                not specified, the original file name will be used. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}/images"
        data = dict(title=title)
        post_files = [
            ("file", (name, fp, content_type))
            for (name, fp, content_type) in upload_files
        ]
        post_headers = {"Authorization": f"Token {self.access_token}"}
        return self._do_request(
            method=POST, url=url, headers=post_headers, data=data, files=post_files
        )

    def update_image(
        self,
        image_id: int,
        course_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
    ):
        """Update an image in the course library.

        Args:
            image_id: Image ID.
            course_id: Course ID.
            title: Image title. Defaults to None.
            description: Image description. Defaults to None.
            sort_order : Image sort order in the course library. Defaults to None.
            metadata: Dictionary of key/value pairs. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/images/{image_id}"
        params: Dict[str, Any] = dict(
            course_id=course_id,
            title=title,
            description=description,
            sort_order=sort_order,
        )
        if metadata is not None:
            params["metadata"] = [
                {"value": v, "label": k} for (k, v) in metadata.items()
            ]
        params = {k: v for k, v in params.items() if v is not None}
        return self._do_request(method=PUT, url=url, headers=self.headers, json=params)

    def get_image(self, image_id: int):
        """Get an image.

        Args:
            image_id: Image ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/images/{image_id}"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def delete_image(self, image_id: int):
        """Delete an image.

        Args:
            image_id: Image ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/images/{image_id}"
        return self._do_request(method=DELETE, url=url, headers=self.headers)
