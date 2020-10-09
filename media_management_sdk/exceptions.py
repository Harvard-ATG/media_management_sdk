class ApiError(IOError):
    pass


class ApiHTTPError(ApiError):
    pass


class ApiBadRequest(ApiHTTPError):
    pass


class ApiForbiddenError(ApiHTTPError):
    pass


class ApiNotFoundError(ApiHTTPError):
    pass
