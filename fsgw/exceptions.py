"""
Custom exceptions for FSGW SDK.

Provides structured error handling for all API operations.
"""

from typing import Any


class FSGWException(Exception):
    """
    Base exception for all FSGW SDK errors.

    All custom exceptions inherit from this base class.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """
        Initialize exception.

        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of the error."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class AuthenticationError(FSGWException):
    """
    Authentication failed.

    Raised when:
    - Login credentials are invalid
    - Token is expired and refresh failed
    - Missing authentication credentials
    """

    pass


class AuthorizationError(FSGWException):
    """
    Authorization failed.

    Raised when:
    - User doesn't have permission to access resource
    - Token doesn't have required scopes
    - RBAC check failed
    """

    pass


class APIError(FSGWException):
    """
    API request failed.

    Raised when:
    - API returns error status
    - Response indicates failure
    - Server returns 4xx or 5xx status
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            response_data: Full response data from API
        """
        super().__init__(message, details=response_data or {})
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self) -> str:
        """String representation including status code."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class ValidationError(FSGWException):
    """
    Request validation failed.

    Raised when:
    - Invalid query parameters
    - Field validation fails
    - Model validation errors
    """

    pass


class NetworkError(FSGWException):
    """
    Network operation failed.

    Raised when:
    - Connection failed
    - DNS resolution failed
    - Network timeout (different from request timeout)
    """

    pass


class TimeoutError(FSGWException):
    """
    Request timeout.

    Raised when:
    - Request exceeds timeout threshold
    - Connection timeout
    - Read timeout
    """

    def __init__(self, message: str, timeout_seconds: float | None = None):
        """
        Initialize timeout error.

        Args:
            message: Error message
            timeout_seconds: Timeout value that was exceeded
        """
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class RateLimitError(FSGWException):
    """
    Rate limit exceeded.

    Raised when:
    - API rate limit reached
    - Too many requests in time window
    """

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        limit: int | None = None,
    ):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            limit: Rate limit threshold
        """
        super().__init__(message)
        self.retry_after = retry_after
        self.limit = limit


class EntityNotFoundError(FSGWException):
    """
    Requested entity not found.

    Raised when:
    - Entity apiUrl doesn't exist
    - Entity was deleted or disabled
    """

    def __init__(self, entity_url: str, message: str | None = None):
        """
        Initialize entity not found error.

        Args:
            entity_url: The apiUrl that wasn't found
            message: Optional custom message
        """
        msg = message or f"Entity not found: {entity_url}"
        super().__init__(msg)
        self.entity_url = entity_url


class MetadataError(FSGWException):
    """
    Metadata operation failed.

    Raised when:
    - Cannot retrieve metadata for entity
    - Metadata validation fails
    - Field not found in metadata
    """

    pass


class QueryError(FSGWException):
    """
    Query operation failed.

    Raised when:
    - Query syntax error
    - Invalid filter operation
    - Query execution failed
    """

    pass


class ConfigurationError(FSGWException):
    """
    SDK configuration error.

    Raised when:
    - Invalid configuration options
    - Missing required configuration
    - Configuration validation failed
    """

    pass
