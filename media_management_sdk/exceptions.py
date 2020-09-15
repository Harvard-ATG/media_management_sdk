class ApiError(IOError):
    pass


class ApiHTTPError(ApiError):
    pass


class ApiForbiddenError(ApiHTTPError):
    pass


class ApiNotFoundError(ApiHTTPError):
    pass
