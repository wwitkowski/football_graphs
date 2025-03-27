class APIRequestLimitExceeded(Exception):
    """Raised when request count reaches limit"""


class APIRequestException(Exception):
    """Raised on request exception"""
