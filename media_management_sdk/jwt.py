import datetime
from typing import Optional

import jwt


def create_jwt(
    client_id: str,
    client_secret: str,
    user_id: str,
    expires_in: float = 3600,
    course_id: Optional[int] = None,
    course_permission: Optional[str] = None,
) -> str:
    """Creates a JSON web token used for authenticating a user.

    Args:
        client_id: Publicly identifies the application or consumer (e.g. consumer key).
        client_secret: Private secret used to securely sign the JWT.
        user_id: The SIS ID of the user making the request.
        expires_in: Number of seconds until the JWT expires. Defaults to 3600 seconds (1 hour).
        course_id: The course ID in the media management API backend (course model PK).
        course_permission: Either "read" or "write". Note that "write" permission is required to create
            collections and upload images.

    Returns:
        A string representing the JWT.
    """
    issued_at = datetime.datetime.utcnow()
    expiration = issued_at + datetime.timedelta(seconds=expires_in)
    payload = {
        "iat": int(issued_at.timestamp()),  # standard claim
        "exp": int(expiration.timestamp()),  # standard claim
        "client_id": client_id,
        "user_id": user_id,
    }
    if course_id is not None:
        payload["course_id"] = course_id
    if course_permission is not None:
        payload["course_permission"] = (
            course_permission if course_permission in ("read", "write") else "read"
        )

    token = jwt.encode(payload, client_secret, algorithm="HS256")

    # back-compat: clients using PyJWT <2.0.0 forces bytes, so try to decode as unicode
    try:
        token = token.decode() # type: ignore
    except (UnicodeDecodeError, AttributeError):
        pass

    return token
