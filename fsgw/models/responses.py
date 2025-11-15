"""
Base response models for FSGW API.

All API responses follow a consistent structure with status, message, and data fields.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# Generic type for data payload
T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response structure for all API calls."""

    status: str = Field(
        ...,
        description="Response status (SUCCESS, ERROR, WARNING, etc.)",
    )
    status_code: int = Field(
        ...,
        alias="statusCode",
        description="HTTP-like status code (200, 400, 500, etc.)",
    )
    message: str = Field(..., description="Human-readable response message")
    timestamp: int | None = Field(
        default=None,
        description="Unix timestamp in milliseconds",
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True

    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.status == "SUCCESS" and 200 <= self.status_code < 300

    def is_error(self) -> bool:
        """Check if response indicates an error."""
        return self.status == "ERROR" or self.status_code >= 400


class DataResponse(BaseResponse, Generic[T]):
    """
    Generic response with typed data payload.

    Examples:
        DataResponse[list[dict]] for list responses
        DataResponse[dict] for single object responses
        DataResponse[None] for responses with no data
    """

    data: T | None = Field(default=None, description="Response data payload")

    def get_data(self) -> T:
        """
        Get response data, raising error if not present.

        Returns:
            Response data

        Raises:
            ValueError: If data is None or response is an error
        """
        if not self.is_success():
            raise ValueError(f"API error: {self.message}")
        if self.data is None:
            raise ValueError("No data in response")
        return self.data


class ErrorResponse(BaseResponse):
    """Error response with additional error details."""

    error: str | None = Field(default=None, description="Error type or code")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details"
    )
    stack_trace: str | None = Field(
        default=None, alias="stackTrace", description="Stack trace for debugging"
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class PaginatedResponse(DataResponse[list[T]], Generic[T]):
    """Response with pagination information."""

    page: int = Field(default=1, description="Current page number (1-indexed)")
    limit: int = Field(default=100, description="Items per page")
    total: int | None = Field(
        default=None, description="Total number of items across all pages"
    )
    has_more: bool = Field(
        default=False, alias="hasMore", description="Whether more pages exist"
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True

    def get_items(self) -> list[T]:
        """Get paginated items."""
        return self.get_data() or []


class ListResponse(DataResponse[list[T]], Generic[T]):
    """Response containing a list of items."""

    def get_items(self) -> list[T]:
        """Get list items, returning empty list if None."""
        return self.get_data() if self.data is not None else []

    def __iter__(self):
        """Allow iteration over response items."""
        return iter(self.get_items())

    def __len__(self) -> int:
        """Get number of items in response."""
        return len(self.get_items())


class SingleResponse(DataResponse[T], Generic[T]):
    """Response containing a single item."""

    def get_item(self) -> T:
        """Get single item."""
        return self.get_data()
