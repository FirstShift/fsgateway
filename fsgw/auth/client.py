"""
Authentication client for FSGW SDK.

Handles authentication, token refresh, and token caching.
"""

import json
from pathlib import Path
from typing import Any

import httpx

from fsgw.auth.models import (
    AuthOutput,
    LoginRequest,
    RefreshTokenInput,
    RefreshTokenOutput,
    TokenInfo,
)


class AuthClient:
    """
    Authentication client for FirstShift Gateway.

    Handles login, token refresh, and token caching with automatic expiry management.
    """

    def __init__(
        self,
        gateway_url: str,
        username: str | None = None,
        password: str | None = None,
        tenant_id: int | None = None,
        cache_file: Path | None = None,
    ):
        """
        Initialize authentication client.

        Args:
            gateway_url: Base URL of the gateway (e.g., https://dev-cloudgateway.firstshift.ai)
            username: Username for authentication
            password: Password for authentication
            tenant_id: Tenant ID for authentication
            cache_file: Optional file path to cache tokens (default: ~/.fsgw_token_cache)
        """
        self.gateway_url = gateway_url.rstrip("/")
        self.username = username
        self.password = password
        self.tenant_id = tenant_id
        self.cache_file = cache_file or Path.home() / ".fsgw_token_cache"

        self._token: TokenInfo | None = None
        self._http_client: httpx.AsyncClient | None = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "AuthClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.close()

    def _load_cached_token(self) -> TokenInfo | None:
        """
        Load token from cache file.

        Returns:
            Cached token or None if cache doesn't exist or is invalid
        """
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            token = TokenInfo.from_dict(data)

            # Check if token is expired
            if token.is_expired():
                return None

            return token
        except Exception:
            # Cache corrupted or format changed - ignore
            return None

    def _save_token_cache(self, token: TokenInfo) -> None:
        """
        Save token to cache file.

        Args:
            token: Token to cache
        """
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(token.to_dict(), f, indent=2)
            # Set restrictive permissions (user read/write only)
            self.cache_file.chmod(0o600)
        except Exception:
            # Caching failed - non-fatal, just continue without cache
            pass

    def _clear_token_cache(self) -> None:
        """Clear token cache file."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except Exception:
            pass

    async def authenticate(self, force: bool = False) -> str:
        """
        Authenticate and get access token.

        Args:
            force: Force re-authentication even if cached token is valid

        Returns:
            Access token string

        Raises:
            ValueError: If credentials are not provided
            httpx.HTTPStatusError: If authentication fails
        """
        # Try to use cached token first
        if not force and self._token is None:
            cached = self._load_cached_token()
            if cached is not None and not cached.is_expired():
                self._token = cached
                return cached.access_token

        # If we have a token and it's not expired, return it
        if not force and self._token is not None and not self._token.is_expired():
            return self._token.access_token

        # If token is expired but we have refresh token, try refresh
        if (
            not force
            and self._token is not None
            and self._token.is_expired()
            and self._token.refresh_token
        ):
            try:
                return await self.refresh_token()
            except Exception:
                # Refresh failed, fall through to re-authenticate
                pass

        # Perform fresh authentication
        if not self.username or not self.password or self.tenant_id is None:
            raise ValueError(
                "Username, password, and tenant_id are required for authentication"
            )

        login_request = LoginRequest(
            username=self.username,
            password=self.password,
            tenant_id=self.tenant_id,
        )

        response = await self.http_client.post(
            f"{self.gateway_url}/auth/login",
            json=login_request.model_dump(by_alias=True),
        )
        response.raise_for_status()

        data = response.json()
        auth_output = AuthOutput(**data["data"])

        # Create token info with expiry tracking
        self._token = TokenInfo.from_auth_output(auth_output)

        # Cache the token
        self._save_token_cache(self._token)

        return self._token.access_token

    async def refresh_token(self) -> str:
        """
        Refresh the access token using the refresh token.

        Returns:
            New access token string

        Raises:
            ValueError: If no token is available to refresh
            httpx.HTTPStatusError: If refresh fails
        """
        if self._token is None:
            raise ValueError("No token available to refresh")

        refresh_request = RefreshTokenInput(
            access_token=self._token.access_token,
            refresh_token=self._token.refresh_token,
        )

        response = await self.http_client.post(
            f"{self.gateway_url}/auth/refresh",
            json=refresh_request.model_dump(by_alias=True),
        )
        response.raise_for_status()

        data = response.json()
        refresh_output = RefreshTokenOutput(**data["data"])

        # Update token with new values
        self._token = TokenInfo(
            access_token=refresh_output.access_token,
            refresh_token=refresh_output.refresh_token,
            expires_at=self._token.expires_at,  # Keep same expiry window
            issued_at=self._token.issued_at,
            user_data=self._token.user_data,
            roles=self._token.roles,
        )

        # Update cache
        self._save_token_cache(self._token)

        return self._token.access_token

    async def get_valid_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        This is the main method to use for getting tokens. It handles:
        - Loading from cache
        - Checking expiry
        - Auto-refreshing if needed
        - Re-authenticating if refresh fails

        Returns:
            Valid access token string

        Raises:
            ValueError: If credentials are not available
            httpx.HTTPStatusError: If authentication fails
        """
        # If no token, authenticate
        if self._token is None:
            return await self.authenticate()

        # If token is expired or about to expire, refresh
        if self._token.is_expired(buffer_seconds=300):  # 5 min buffer
            try:
                return await self.refresh_token()
            except Exception:
                # Refresh failed, re-authenticate
                return await self.authenticate(force=True)

        return self._token.access_token

    def logout(self) -> None:
        """
        Logout and clear cached token.

        This clears the in-memory token and removes the cache file.
        """
        self._token = None
        self._clear_token_cache()

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated with a valid token."""
        return self._token is not None and not self._token.is_expired()

    @property
    def current_user(self) -> Any | None:
        """Get current authenticated user data."""
        return self._token.user_data if self._token else None

    @property
    def current_roles(self) -> tuple[str, ...]:
        """Get current user roles."""
        return self._token.roles if self._token else tuple()
