import datetime
from typing import Optional

import jwt


def create_jwt(
    client_id: str,
    client_secret: str,
    user_id: str,
    course_id: Optional[int] = None,
    course_permission: Optional[str] = None,
    expires_in: Optional[int] = 36000,
) -> str:
    """Creates a JSON web token used for authenticating a user.

    Args:
        client_id: Publicly identifies the application or consumer (e.g. consumer key).
        client_secret: Private secret used to securely sign the JWT.
        user_id: The SIS ID of the user making the request.
        course_id: The course ID in the media management API backend (course model PK).
        course_permission: Either "read" or "write". Note that "write" permission is required to create
            collections and upload images.
        expires_in: Number of seconds until the JWT expires. Defaults to 10 hours.

    Returns:
        A string representing the JWT.
    """
    issued_at = datetime.datetime.utcnow()
    expiration = issued_at + datetime.timedelta(seconds=expires_in)
    payload = {
        "iat": int(issued_at.timestamp()),   # standard claim
        "exp": int(expiration.timestamp()),  # standard claim
        "client_id": client_id,
        "user_id": user_id,
    }
    if course_id is not None:
        payload["course_id"] = course_id
    if course_permission is not None:
        payload["course_permission"] = course_permission if course_permission in ("read", "write") else "read"

    return jwt.encode(payload, client_secret, algorithm="HS256")
