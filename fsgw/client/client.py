"""
FSGWClient - FirstShift API Gateway Client.

Provides a type-safe SDK for interacting with the FirstShift API Gateway.
"""

import asyncio
import base64
import json
from datetime import UTC, datetime
from typing import Any

import httpx
import logfire
from pydantic import BaseModel, Field, PrivateAttr, field_validator

from fsgw.auth.models import AuthOutput, AuthUserData, LoginRequest
from fsgw.client.models import APIResponse, AuthToken, HTTPStatus
from fsgw.models import EndpointsResponse, MetadataResponse, QueryRequest, QueryResponse


class FSGWClient(BaseModel):
    """
    FirstShift API Gateway Client.

    Provides discovery, metadata, and query capabilities for any entity
    exposed by the FirstShift platform.

    Usage:
        >>> client = FSGWClient(
        ...     gateway_url="https://dev-cloudgateway.firstshift.ai",
        ...     tenant_id=7,
        ...     username="user@example.com",
        ...     password="secret"
        ... )
        >>>
        >>> # Authentication happens automatically on first API call
        >>> endpoints = await client.list_endpoints()
        >>>
        >>> # Get metadata for an entity
        >>> metadata = await client.get_metadata(entity="products")
        >>>
        >>> # Query data
        >>> results = await client.query(entity="products", filters={"status": "active"})
    """

    # Required configuration
    gateway_url: str = Field(
        ...,
        description="FirstShift API gateway URL",
        examples=["https://dev-cloudgateway.firstshift.ai"],
    )

    tenant_id: int = Field(
        ...,
        ge=1,
        description="Tenant identifier",
        examples=[7, 12345],
    )

    username: str = Field(
        ...,
        description="User login name for authentication",
        examples=["user@example.com"],
    )

    password: str = Field(
        ...,
        description="User password for authentication",
    )

    # Optional - will be set after authentication
    api_key: str | None = Field(
        default=None,
        description="API access token (set automatically after authentication)",
    )

    # Optional configuration
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )
    auto_refresh: bool = Field(
        default=True,
        description="Automatically refresh access tokens before they expire.",
    )
    refresh_lead_time: int = Field(
        default=300,
        ge=0,
        le=3600,
        description="Seconds before expiration when a proactive refresh is triggered.",
    )

    # Internal state
    _http_client: httpx.AsyncClient | None = PrivateAttr(default=None)
    _authenticated: bool = PrivateAttr(default=False)
    _auth_token: AuthToken | None = PrivateAttr(default=None)
    _user_info: AuthUserData | None = PrivateAttr(default=None)
    _refresh_lock: asyncio.Lock | None = PrivateAttr(default=None)

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    @field_validator("gateway_url")
    @classmethod
    def validate_gateway_url(cls, v: str) -> str:
        """Validate and normalize gateway URL."""
        v = v.strip()
        if not v:
            raise ValueError("Gateway URL cannot be empty")
        if not v.startswith(("http://", "https://")):
            raise ValueError("Gateway URL must start with http:// or https://")
        return v.rstrip("/")

    def __init__(self, **data: Any) -> None:
        """
        Initialize client.

        Args:
            **data: Client configuration parameters
        """
        super().__init__(**data)

        # Each client maintains its own refresh lock to prevent concurrent refresh calls.
        object.__setattr__(self, "_refresh_lock", asyncio.Lock())

        # Initialize HTTP client
        object.__setattr__(
            self,
            "_http_client",
            httpx.AsyncClient(
                base_url=self.gateway_url,
                timeout=httpx.Timeout(self.timeout),
            ),
        )

    @property
    def auth_token(self) -> AuthToken | None:
        """Return the current authentication token details, if available."""
        return self.__pydantic_private__.get("_auth_token")

    @property
    def user_info(self) -> AuthUserData | None:
        """Return metadata about the authenticated user."""
        return self.__pydantic_private__.get("_user_info")

    async def _make_request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
        *,
        include_access_token: bool = True,
    ) -> APIResponse:
        """
        Core HTTP request method.

        Args:
            method: HTTP method (GET, POST)
            path: Endpoint path
            params: Query parameters
            json_data: Request body as JSON
            include_access_token: Whether to include access token header

        Returns:
            APIResponse with data or error
        """
        # Ensure authentication before making request
        if include_access_token and not self.__pydantic_private__.get("_authenticated", False):
            await self._authenticate()

        with logfire.span(
            "fsgw.request",
            method=method,
            path=path,
            tenant_id=self.tenant_id,
        ):
            response: httpx.Response | None = None

            try:
                headers = {}
                if include_access_token and self.api_key:
                    headers["access-token"] = self.api_key

                response = await self._http_client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json_data,
                    headers=headers,
                )
            except httpx.TimeoutException as e:
                return APIResponse.error_response(
                    error=f"Request timeout after {self.timeout}s",
                    error_code="TIMEOUT",
                    status_code=408,
                )
            except httpx.NetworkError as e:
                return APIResponse.error_response(
                    error=f"Network error: {str(e)}",
                    error_code="NETWORK_ERROR",
                    status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                )
            except Exception as e:
                return APIResponse.error_response(
                    error=str(e),
                    error_code="UNEXPECTED_ERROR",
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

            if response is None:
                return APIResponse.error_response(
                    error="Failed to receive response from FirstShift API",
                    status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                )

            logfire.info(
                f"{method} {path} -> {response.status_code}",
                status_code=response.status_code,
            )

            if response.status_code == 200:
                data = response.json()
                return APIResponse.success_response(data=data)

            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and "error" in error_data:
                    error_msg = error_data["error"]
            except Exception:
                pass

            return APIResponse.error_response(
                error=error_msg,
                status_code=response.status_code,
            )

    async def _authenticate(self) -> None:
        """
        Perform authentication with stored credentials.

        Called automatically on first SDK method call if not already authenticated.
        Stores the access token for subsequent requests.

        Raises:
            ValueError: If authentication fails
        """
        # Check if already authenticated via __pydantic_private__
        if self.__pydantic_private__.get("_authenticated", False):
            return

        # Build login request
        login_request = LoginRequest(
            username=self.username,
            password=self.password,
            tenant_id=self.tenant_id,
        )

        # Call authenticate endpoint
        response = await self._make_request(
            method="POST",
            path="/auth/login",
            json_data=login_request.model_dump(by_alias=True),
            include_access_token=False,
        )

        if not response.success or not response.data:
            error_msg = response.error or "Authentication failed"
            raise ValueError(f"Authentication failed: {error_msg}")

        # Extract auth data from response
        auth_data = AuthOutput(**response.data.get("data", {}))

        self._apply_login_metadata(auth_data)

    def _apply_login_metadata(self, auth_data: AuthOutput) -> None:
        """Persist login metadata (tokens, user info)."""
        self._update_auth_token(
            access_token=auth_data.access_token,
            refresh_token=auth_data.refresh_token,
        )

        private = object.__getattribute__(self, "__pydantic_private__")
        private["_user_info"] = auth_data.user_data

    def _update_auth_token(self, *, access_token: str, refresh_token: str | None) -> AuthToken:
        """Update stored auth token and access key."""
        token = self._build_auth_token(access_token=access_token, refresh_token=refresh_token)
        object.__setattr__(self, "api_key", token.access_token)

        private = object.__getattribute__(self, "__pydantic_private__")
        private["_auth_token"] = token
        private["_authenticated"] = True
        return token

    def _build_auth_token(self, *, access_token: str, refresh_token: str | None) -> AuthToken:
        """Construct an AuthToken with inferred expiry information."""
        expires_at, expires_in = self._extract_expiration_info(access_token)
        token_kwargs: dict[str, Any] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "issued_at": datetime.utcnow(),
        }

        if expires_at is not None:
            token_kwargs["expires_at"] = expires_at
        if expires_in is not None:
            token_kwargs["expires_in"] = expires_in

        return AuthToken(**token_kwargs)

    def _extract_expiration_info(self, access_token: str) -> tuple[datetime | None, int | None]:
        """Decode JWT expiry details."""
        payload = self._decode_jwt_payload(access_token)
        if not payload:
            return (None, None)

        exp = payload.get("exp")
        if not isinstance(exp, (int, float)):
            return (None, None)

        expires_at = datetime.fromtimestamp(int(exp), tz=UTC).replace(tzinfo=None)
        remaining = expires_at - datetime.utcnow()
        expires_in = max(int(remaining.total_seconds()), 0)
        return (expires_at, expires_in)

    def _decode_jwt_payload(self, token: str) -> dict[str, Any] | None:
        """Decode JWT payload without verifying signature."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            payload_segment = parts[1]
            padding = "=" * (-len(payload_segment) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_segment + padding)
            return json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return None

    # API #1 - List All Available Endpoints
    async def list_endpoints(self) -> APIResponse[EndpointsResponse]:
        """
        List all available API endpoints (API #1).

        Returns all API groups and entities exposed by the platform.

        Returns:
            APIResponse[EndpointsResponse]: Response with all endpoints

        Example:
            >>> endpoints = await client.list_endpoints()
            >>> if endpoints.success:
            ...     for group in endpoints.data.groups:
            ...         print(f"Group: {group.name}")
            ...         for entity in group.entities:
            ...             print(f"  - {entity.name}: {entity.endpoint}")
        """
        response = await self._make_request(
            method="GET",
            path="/api/v1/endpoints",
        )

        if not response.success:
            return APIResponse.error_response(
                error=response.error or "Failed to list endpoints",
                status_code=response.status_code,
            )

        # Parse response data into EndpointsResponse
        try:
            endpoints_data = EndpointsResponse(**response.data)
            return APIResponse.success_response(data=endpoints_data)
        except Exception as e:
            return APIResponse.error_response(
                error=f"Failed to parse endpoints response: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    # API #2 - Get Metadata for Any Entity
    async def get_metadata(self, entity: str) -> APIResponse[MetadataResponse]:
        """
        Get metadata for a specific entity (API #2).

        Returns field-level schema information including data types,
        constraints, and primary keys.

        Args:
            entity: Entity name (e.g., "products", "customers")

        Returns:
            APIResponse[MetadataResponse]: Response with entity metadata

        Example:
            >>> metadata = await client.get_metadata(entity="products")
            >>> if metadata.success:
            ...     for field in metadata.data.fields:
            ...         print(f"{field.name}: {field.data_type}")
        """
        response = await self._make_request(
            method="GET",
            path=f"/api/v1/metadata/{entity}",
        )

        if not response.success:
            return APIResponse.error_response(
                error=response.error or f"Failed to get metadata for {entity}",
                status_code=response.status_code,
            )

        # Parse response data into MetadataResponse
        try:
            metadata_data = MetadataResponse(**response.data)
            return APIResponse.success_response(data=metadata_data)
        except Exception as e:
            return APIResponse.error_response(
                error=f"Failed to parse metadata response: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    # API #3 - Query Data for Any Entity
    async def query(
        self,
        entity: str,
        filters: dict[str, Any] | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 100,
        fields: list[str] | None = None,
    ) -> APIResponse[QueryResponse]:
        """
        Query data for a specific entity (API #3).

        Supports fully generic querying with filters, sorting, pagination,
        and optional field projections.

        Args:
            entity: Entity name (e.g., "products", "customers")
            filters: Filter conditions as key-value pairs
            sort_by: Field name to sort by
            sort_order: Sort order ("asc" or "desc")
            page: Page number (1-indexed)
            limit: Records per page (1-1000)
            fields: Fields to include in response (projection)

        Returns:
            APIResponse[QueryResponse]: Response with query results

        Example:
            >>> # Simple query
            >>> results = await client.query(entity="products")
            >>>
            >>> # Query with filters and sorting
            >>> results = await client.query(
            ...     entity="products",
            ...     filters={"category": "electronics", "price": {"$gt": 100}},
            ...     sort_by="price",
            ...     sort_order="desc",
            ...     limit=20
            ... )
            >>>
            >>> if results.success:
            ...     for item in results.data.items:
            ...         print(item)
        """
        # Build query request
        query_request = QueryRequest(
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit,
            fields=fields,
        )

        response = await self._make_request(
            method="POST",
            path=f"/api/v1/query/{entity}",
            json_data=query_request.model_dump(exclude_none=True),
        )

        if not response.success:
            return APIResponse.error_response(
                error=response.error or f"Failed to query {entity}",
                status_code=response.status_code,
            )

        # Parse response data into QueryResponse
        try:
            query_data = QueryResponse(**response.data)
            return APIResponse.success_response(data=query_data)
        except Exception as e:
            return APIResponse.error_response(
                error=f"Failed to parse query response: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self._http_client:
            await self._http_client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
