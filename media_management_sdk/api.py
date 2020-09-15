import logging
import json
import requests

from media_management_sdk.exceptions import (
    ApiError,
    ApiHTTPError,
    ApiForbiddenError,
    ApiNotFoundError,
)

logger = logging.getLogger(__name__)

GET, POST, PUT, DELETE = ("get", "post", "put", "delete")

DEFAULT_TIMEOUT = 10


class API(object):
    def __init__(self, base_url=None, access_token=None):
        """API constructor.

        Args:
            base_url (str, optional): The API base URL that will prefix all
                endpoint requests. Defaults to None.
            access_token (str, optional): The API access token to use for requests
                that require authorization. Defaults to None.
        """
        self.base_url = base_url
        self.access_token = access_token

    @property
    def headers(self):
        """Get the HTTP headers needed for API requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.access_token is not None:
            headers["Authorization"] = f"Token {self.access_token}"
        return headers

    def _do_request(self, method=GET, url=None, **kwargs):
        """Performs the HTTP request.

        This method centralizes exception handling and logging and
        sets some defaults for all requests (e.g. timeout).

        Args:method (str): One of: get, post, put, delete. Defaults to get.
            url (str): The endpoint URL. Defaults to "".
            **kwargs: Arbitrary keyword arguments. These are passed directly
                to the requests method (e.g. get(), post(), etc).

        Raises:
            ValueError: If the method is invalid.
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

        # Log the request, omitting headers which may contain auth credentials
        log_kwargs = json.dumps({k: kwargs[k] for k in kwargs if k != "headers"})
        logger.info(f"API request [{method} {url}] {log_kwargs}")

        try:
            r = request_callable(url, **kwargs)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.exception("HTTP error")
            status_code = e.response.status_code
            if status_code == 403:
                raise ApiForbiddenError
            elif status_code == 404:
                raise ApiNotFoundError
            else:
                raise ApiHTTPError(f"HTTP error status code: {status_code}")
        except requests.exceptions.RequestException as e:
            logger.exception("Request error")
            raise ApiError("Request exception: " + str(e))

        try:
            data = r.json()
        except ValueError as e:
            logger.exception("No JSON object could be decoded")
            raise ApiError("No JSON object could be decoded")

        return data

    def obtain_token(
        self,
        client_id=None,
        client_secret=None,
        user_id=None,
        course_id=None,
        course_permission=None,
    ):
        """
        Obtains a temporary access token.

        Args:client_id (str): Identifies the client application. Obtained from API /admin.
            client_secret (str): Identifies the client application. Obtained from API /admin.
            user_id (str): The SIS User ID.
            course_id (str, optional): The PK of the course object that exists in the API. Used to
                grant the user access to the course if they didn't create it.
            course_permission (str, optional): One of "read" or "write", defaults to "read". Used
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
            params["course_id"] = course_id
        if course_id and course_permission:
            params["course_permission"] = course_permission
        return self._do_request(method=POST, url=url, headers=self.headers, json=params)

    def list_courses(
        self,
        lti_context_id=None,
        lti_tool_consumer_instance_guid=None,
        canvas_course_id=None,
        sis_course_id=None,
        title=None,
    ):
        """List courses.

        Filter the list of courses by providing a value for one or more of the course attributes.
        In an LTI context, the *lti_context_id* and *lti_tool_consumer_instance_guid*
        are commonly used to find a particular course.

        Args:
            title (str): Course title. Defaults to None.
            sis_course_id (str, optional): SIS course ID. Defaults to None.
            canvas_course_id (str, optional): Canvas course ID. Defaults to None.
            lti_context_id (str, optional): LTI context ID. Defaults to None.
            lti_tool_consumer_instance_guid (str, optional): LTI consumer instance GUID. Defaults to None.

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

    def search_courses(self, text=""):
        """Search courses.

        Args:
            text (str): Search text. Defaults to None.

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

    def get_course(self, course_id):
        """Get a course.

        Args:
            course_id (int): Course ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def create_course(
        self,
        title,
        sis_course_id=None,
        canvas_course_id=None,
        lti_context_id=None,
        lti_tool_consumer_instance_guid=None,
        lti_tool_consumer_instance_name=None,
        lti_context_title=None,
        lti_context_label=None,
    ):
        """Create a course.

        Args:
            title (str): Course title.
            sis_course_id (str, optional): SIS course ID. Defaults to None.
            canvas_course_id (str, optional): Canvas course ID. Defaults to None.
            lti_context_id (str, optional): LTI context ID. Defaults to None.
            lti_tool_consumer_instance_guid (str, optional): Tool consumer instance GUID. Defaults to None.
            lti_tool_consumer_instance_name (str, optional): Tool consumer instance Name. Defaults to None.
            lti_context_title (str, optional): LTI context title. Defaults to None.
            lti_context_label (str, optional): LTI context label. Defaults to None.

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
        return self._do_request(method=POST, url=url, headers=self.headers, json=params)

    def update_course(
        self,
        course_id,
        title=None,
        sis_course_id=None,
        canvas_course_id=None,
        lti_context_id=None,
        lti_tool_consumer_instance_guid=None,
        lti_tool_consumer_instance_name=None,
        lti_context_title=None,
        lti_context_label=None,
    ):
        """Create a course.

        Args:
            course_id (int): Course ID.
            title (str, optional): Course title. Defaults to None.
            sis_course_id (str, optional): SIS course ID. Defaults to None.
            canvas_course_id (str, optional): Canvas course ID. Defaults to None.
            lti_context_id (str, optional): LTI context ID. Defaults to None.
            lti_tool_consumer_instance_guid (str, optional): Tool consumer instance GUID. Defaults to None.
            lti_tool_consumer_instance_name (str, optional): Tool consumer instance Name. Defaults to None.
            lti_context_title (str, optional): LTI context title. Defaults to None.
            lti_context_label (str, optional): LTI context label. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}"
        params = dict(
            lti_context_id=lti_context_id,
            lti_tool_consumer_instance_guid=lti_tool_consumer_instance_guid,
            lti_context_title=lti_context_title,
            lti_context_label=lti_context_label,
            title=title,
            sis_course_id=sis_course_id,
            canvas_course_id=canvas_course_id,
        )
        return self._do_request(method=PUT, url=url, headers=self.headers, json=params)

    def delete_course(self, course_id):
        """Deletes a course.

        Args:
            course_id (int): Course ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}"
        return self._do_request(method=DELETE, url=url, headers=self.headers)

    def copy_course(self, src_course_id, dest_course_id):
        """Copy a course and all of its resources.

        Note that the destination course must already exist.

        Args:
            src_course_id (int): Course that is the source of the copy.
            dest_course_id (int): Course that is the destination of the copy.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{dest_course_id}/course_copy"
        params = dict(source_id=src_course_id)
        return self._do_request(method=POST, url=url, headers=self.headers, json=params)

    def list_collections(self, course_id):
        """Lists collections in a course.

        Args:
            course_id (int): Course ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/collections"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def get_collection(self, collection_id):
        """Get collection details.

        Args:
            collection_id (int): Collection ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/collections/{collection_id}"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def get_collection_images(self, collection_id):
        """Get collection images.

        Args:
            collection_id (int): Collection ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/collections/{collection_id}/images"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def create_collection(self, course_id, title, description=None):
        """Create a collection.

        Args:
            collection_id (int): Collection ID.
            course_id (int): Course ID.
            title (str): Collection title.
            description (str, optional): Collection description. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/collections"
        params = dict(course_id=course_id, title=title, description=description)
        return self._do_request(method=POST, url=url, headers=self.headers, json=params)

    def update_collection(
        self,
        collection_id,
        title=None,
        description=None,
        sort_order=None,
        course_image_ids=None,
    ):
        """Update a collection.

        Args:
            title (str): Collection title.
            description (str, optional): Collection description. Defaults to None.
            sort_order (int, optional): Collection sort order. Defaults to None.
            course_image_ids (list, optional): The list of images that should be part of this collection,
                which should reference images from the course image library (course image IDs). Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/collections/{collection_id}"
        params = dict(
            title=title,
            description=description,
            sort_order=sort_order,
            course_image_ids=course_image_ids,
        )
        return self._do_request(method=PUT, url=url, headers=self.headers, json=params)

    def delete_collection(self, collection_id):
        """Deletes a collection.

        Args:
            collection_id (int): Collection ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/collections/{collection_id}"
        return self._do_request(method=DELETE, url=url, headers=self.headers)

    def upload_image(self, course_id, upload_file, title=None):
        """Upload a single image to the course.

        Args:
            course_id (int): Course ID.
            upload_file (file): File must implement read() and have "name" and "content_type" attributes.
            title (str, optional): Title to use for the file. Note that if
                not specified, the original file name will be used. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        return self.upload_images(course_id, [upload_file], title=title)

    def upload_images(self, course_id, upload_files, title=None):
        """Upload images to the course.

        Args:
            course_id (int): Course ID.
            upload_files (list): List of files to upload. Each file must implement
                read() and have "name" and "content_type" attributes.
            title (str, optional): Title to use for the file or list of files. Note that if
                not specified, the original file name will be used. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/courses/{course_id}/images"
        data = dict(title=title)
        post_files = []
        for f in upload_files:
            file_tuple = (f.name, f.read(), f.content_type)
            post_files.append(("file", file_tuple))  # the field name must be "files"
        return self._do_request(
            method=POST, url=url, headers=self.headers, data=data, files=post_files
        )

    def update_image(
        self,
        image_id,
        title=None,
        description=None,
        sort_order=None,
        metadata=None,
    ):
        """Update an image in the course library.

        Args:
            image_id (int): Image ID.
            title (str, optional): Image title. Defaults to None.
            description (str, optional): Image description. Defaults to None.
            sort_order (int, optional): Image sort order in the course library. Defaults to None.
            metadata (dict, optional): Dictionary of key/value pairs. Defaults to None.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/images/{image_id}"
        params = dict(title=title, description=description, sort_order=sort_order)
        if metadata is not None:
            params["metadata"] = [
                {"value": value, "label": key} for (key, value) in metadata.items()
            ]
        return self._do_request(method=PUT, url=url, headers=self.headers, json=params)

    def get_image(self, image_id):
        """Get an image.

        Args:
            image_id (int): Image ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/images/{image_id}"
        return self._do_request(method=GET, url=url, headers=self.headers)

    def delete_image(self, image_id):
        """Delete an image.

        Args:
            image_id (int): Image ID.

        Returns:
            Response data.

        Raises:
            ApiError: Raised on 4XX or 5XX error response.
        """
        url = f"{self.base_url}/images/{image_id}"
        return self._do_request(method=DELETE, url=url, headers=self.headers)
