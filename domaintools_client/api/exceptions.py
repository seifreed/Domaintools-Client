"""Custom exceptions for DomainTools API client."""


class DomainToolsError(Exception):
    """Base exception for DomainTools API errors."""

    pass


class AuthenticationError(DomainToolsError):
    """Raised when authentication fails."""

    pass


class RateLimitError(DomainToolsError):
    """Raised when rate limit is exceeded."""

    pass


class InvalidRequestError(DomainToolsError):
    """Raised when the request is invalid."""

    pass


class NotFoundError(DomainToolsError):
    """Raised when the requested resource is not found."""

    pass
