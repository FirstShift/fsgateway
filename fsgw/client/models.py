"""
Core HTTP models and response types for FSGW client.
"""

from datetime import UTC, datetime
from enum import IntEnum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HTTPStatus(IntEnum):
    """HTTP status codes."""

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper.

    All SDK methods return APIResponse[T] where T is the expected data type.
    """

    success: bool = Field(description="Whether the request was successful")
    data: T | None = Field(default=None, description="Response data if successful")
    error: str | None = Field(default=None, description="Error message if failed")
    error_code: str | None = Field(default=None, description="Error code if failed")
    status_code: int = Field(description="HTTP status code")
    message: str | None = Field(default=None, description="Additional message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None),
        description="Response timestamp",
    )

    @property
    def status(self) -> str:
        """Human-readable status."""
        return "success" if self.success else "error"

    @classmethod
    def success_response(
        cls,
        data: T,
        status_code: int = HTTPStatus.OK,
        message: str | None = None,
    ) -> "APIResponse[T]":
        """Create a successful response."""
        return cls(
            success=True,
            data=data,
            status_code=status_code,
            message=message,
        )

    @classmethod
    def error_response(
        cls,
        error: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        error_code: str | None = None,
        message: str | None = None,
    ) -> "APIResponse[T]":
        """Create an error response."""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            status_code=status_code,
            message=message,
            data=None,
        )


class AuthToken(BaseModel):
    """Authentication token with expiration info."""

    access_token: str = Field(description="JWT access token")
    refresh_token: str | None = Field(default=None, description="Refresh token if available")
    issued_at: datetime = Field(description="Token issue timestamp")
    expires_at: datetime | None = Field(default=None, description="Token expiration timestamp")
    expires_in: int | None = Field(default=None, description="Seconds until expiration")

    def is_expired(self) -> bool:
        """Check if token has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() >= self.expires_at

    def expires_soon(self, lead_time_seconds: int = 300) -> bool:
        """Check if token expires within lead_time_seconds."""
        if self.expires_at is None:
            return False
        threshold = datetime.utcnow()
        threshold = threshold.replace(microsecond=0)
        expires = self.expires_at.replace(microsecond=0)
        remaining = (expires - threshold).total_seconds()
        return remaining <= lead_time_seconds


class ClientError(Exception):
    """Base exception for client errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(ClientError):
    """Authentication failed."""

    pass


class ValidationError(ClientError):
    """Request validation failed."""

    pass


class NotFoundError(ClientError):
    """Resource not found."""

    pass


class ServerError(ClientError):
    """Server error occurred."""

    pass
