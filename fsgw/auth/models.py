"""
Authentication models for FSGW SDK.

Adapted from shiftfm authentication to work with FirstShift Gateway.
Uses the exact same auth mechanism and models as shiftfm.
"""

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Internal login request payload with API field names."""

    username: str = Field(..., serialization_alias="userName")
    password: str = Field(...)
    tenant_id: int = Field(..., serialization_alias="tenantId")


class AuthUserData(BaseModel):
    """User metadata from authentication response."""

    id: str | None = None
    username: str | None = None
    email: str | None = None
    first_name: str | None = Field(None, alias="firstName")
    last_name: str | None = Field(None, alias="lastName")
    tenant_uuid: str | None = Field(None, alias="tenantId")
    data: dict[str, Any] | None = None

    class Config:
        """Allow and preserve unknown fields for forward compatibility."""

        populate_by_name = True
        extra = "allow"


class AuthOutput(BaseModel):
    """Authentication response data - matches shiftfm exactly."""

    access_token: str = Field(
        ...,
        alias="access-token",  # IMPORTANT: Uses hyphen, not camelCase!
        min_length=1,
        description="JWT access token for authenticated API requests",
    )
    refresh_token: str = Field(
        ...,
        alias="refresh-token",  # IMPORTANT: Uses hyphen, not camelCase!
        min_length=1,
        description="Refresh token that can be exchanged for a new access token",
    )
    user_data: AuthUserData | None = Field(
        default=None,
        alias="userData",
        description="Authenticated user profile information",
    )
    roles: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Roles granted to the user within FirstShift",
    )
    alerts_security_details: str | None = Field(
        default=None,
        alias="alertsSecurityDetails",
        description="Opaque token used for security alerts in downstream services",
    )
    setup_complete: bool | None = Field(
        default=None,
        alias="setupComplete",
        description="Indicates whether onboarding setup is complete for the user",
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True  # Allow both snake_case and API aliases

    @field_validator("roles", mode="before")
    @classmethod
    def _coerce_roles(cls, value: Any) -> tuple[str, ...]:
        """Normalize roles into a tuple of strings."""
        if value is None:
            return tuple()
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",")]
            return tuple(item for item in items if item)
        if isinstance(value, Iterable):
            return tuple(str(item).strip() for item in value if str(item).strip())
        return tuple()

    @field_validator("setup_complete", mode="before")
    @classmethod
    def _coerce_setup_complete(cls, value: Any) -> bool | None:
        """Normalize truthy values (1, 'true', etc.) to boolean."""
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            value = value.strip().lower()
            if value in {"1", "true", "yes", "y"}:
                return True
            if value in {"0", "false", "no", "n"}:
                return False
        return None


class RefreshTokenInput(BaseModel):
    """Refresh token request payload."""

    access_token: str = Field(
        ...,
        alias="accessToken",
        min_length=1,
        description="Current (possibly expired) access token",
    )
    refresh_token: str = Field(
        ...,
        alias="refreshToken",
        min_length=1,
        description="Refresh token issued during login",
    )

    class Config:
        populate_by_name = True


class RefreshTokenOutput(BaseModel):
    """Refresh token response data."""

    access_token: str = Field(
        ...,
        alias="access-token",
        min_length=1,
        description="Newly issued access token",
    )
    refresh_token: str = Field(
        ...,
        alias="refresh-token",
        min_length=1,
        description="Refresh token to use for subsequent refreshes",
    )

    class Config:
        populate_by_name = True


class TokenInfo(BaseModel):
    """Token information with expiry tracking."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    expires_at: datetime | None = Field(
        default=None, description="Token expiration timestamp"
    )
    issued_at: datetime = Field(
        default_factory=datetime.utcnow, description="Token issue timestamp"
    )
    user_data: AuthUserData | None = Field(
        default=None, description="User information"
    )
    roles: tuple[str, ...] = Field(
        default_factory=tuple, description="User roles"
    )

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """
        Check if token is expired or about to expire.

        Args:
            buffer_seconds: Consider token expired this many seconds before actual expiry

        Returns:
            True if token is expired or will expire within buffer_seconds
        """
        if self.expires_at is None:
            # If we don't know expiry, parse JWT or assume not expired
            return False

        now = datetime.utcnow()
        buffer = timedelta(seconds=buffer_seconds)
        return now >= (self.expires_at - buffer)

    def time_until_expiry(self) -> timedelta | None:
        """
        Get time remaining until token expires.

        Returns:
            Time until expiry, or None if expiry is unknown
        """
        if self.expires_at is None:
            return None

        now = datetime.utcnow()
        remaining = self.expires_at - now
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    @classmethod
    def from_auth_output(
        cls, auth_output: AuthOutput, expires_in_seconds: int | None = None
    ) -> "TokenInfo":
        """
        Create TokenInfo from AuthOutput.

        Args:
            auth_output: Authentication response
            expires_in_seconds: Token lifetime in seconds (default: 8 hours)

        Returns:
            TokenInfo instance
        """
        expires_in = expires_in_seconds or (8 * 60 * 60)  # Default 8 hours
        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(seconds=expires_in)

        return cls(
            access_token=auth_output.access_token,
            refresh_token=auth_output.refresh_token,
            expires_at=expires_at,
            issued_at=issued_at,
            user_data=auth_output.user_data,
            roles=auth_output.roles,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "issued_at": self.issued_at.isoformat(),
            "user_data": self.user_data.model_dump() if self.user_data else None,
            "roles": list(self.roles),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenInfo":
        """Create from dictionary (for cache loading)."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            issued_at=datetime.fromisoformat(data["issued_at"]),
            user_data=AuthUserData(**data["user_data"]) if data.get("user_data") else None,
            roles=tuple(data.get("roles", [])),
        )
