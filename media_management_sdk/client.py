from media_management_sdk.api import API


class Client(object):
    """
    Client is a wrapper for interacting with the API.
    """

    def __init__(self, client_id=None, client_secret=None, base_url=None):
        if client_id is None or client_secret is None:
            raise ValueError("Missing client credentials")
        if base_url is None:
            raise ValueError("Missing base URL to use for API requests")

        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.api = API(base_url=base_url)
        self.access_token = None

    def authenticate(self, user_id, course_id=None, course_permission=None):
        """
        Authenticate with the API by supplying client credentials and obtaining
        a token tied to the user.
        """
        response = self.api.obtain_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_id=user_id,
            course_id=course_id,
            course_permission=course_permission,
        )
        self.api.access_token = response["access_token"]

    def find_or_create_course(self):
        pass
