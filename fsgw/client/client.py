"""
Main FSGW SDK client.

Provides high-level interface to all FirstShift Gateway APIs.
"""

from typing import Any

from fsgw.auth.client import AuthClient
from fsgw.client.base import BaseClient
from fsgw.exceptions import APIError, EntityNotFoundError, MetadataError, QueryError
from fsgw.models.endpoints import EndpointEntity, EndpointsResponse
from fsgw.models.metadata import FieldMetadata, MetadataResponse
from fsgw.models.query import QueryRequest, QueryResponse
from fsgw.models.responses import DataResponse


class FSGWClient(BaseClient):
    """
    Main client for FirstShift Gateway API.

    Provides high-level access to:
    - API #1: Discovery (list all entities)
    - API #2: Metadata (get field information)
    - API #3: Query (retrieve entity data)

    Features:
    - Automatic authentication and token refresh
    - Connection pooling and retry logic
    - Type-safe responses with Pydantic models
    - Context manager support

    Example:
        ```python
        async with FSGWClient(
            gateway_url="https://dev-cloudgateway.firstshift.ai",
            username="user",
            password="pass",
            tenant_id=7,
        ) as client:
            # List all entities
            entities = await client.list_apis()

            # Get metadata
            metadata = await client.get_metadata("ops/auditTrail")

            # Query data
            query = QueryRequest().add_filter("tenantId", "=", 7).limit(10)
            results = await client.query("ops/auditTrail", query)
        ```
    """

    def __init__(
        self,
        gateway_url: str,
        username: str | None = None,
        password: str | None = None,
        tenant_id: int | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
    ):
        """
        Initialize FSGW client.

        Args:
            gateway_url: Base URL of the gateway (e.g., https://dev-cloudgateway.firstshift.ai)
            username: Username for authentication
            password: Password for authentication
            tenant_id: Tenant ID for authentication
            timeout: Default timeout in seconds
            max_retries: Maximum number of retry attempts
            max_connections: Maximum number of concurrent connections
            max_keepalive_connections: Maximum number of keep-alive connections
        """
        super().__init__(
            base_url=gateway_url,
            timeout=timeout,
            max_retries=max_retries,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

        # Initialize auth client
        self._auth_client = AuthClient(
            gateway_url=gateway_url,
            username=username,
            password=password,
            tenant_id=tenant_id,
        )

        # Cache for discovered entities
        self._entities_cache: list[EndpointEntity] | None = None

    async def close(self) -> None:
        """Close HTTP client and auth client."""
        await super().close()
        await self._auth_client.close()

    async def _get_auth_headers(self) -> dict[str, str]:
        """
        Get authentication headers with valid token.

        Returns:
            Dictionary with access-token header

        Raises:
            AuthenticationError: If authentication fails
        """
        token = await self._auth_client.get_valid_token()
        return {"access-token": token}

    # -------------------------------------------------------------------------
    # API #1: Discovery - List all entities
    # -------------------------------------------------------------------------

    async def list_apis(self, use_cache: bool = True) -> list[EndpointEntity]:
        """
        List all available API entities (API #1).

        Args:
            use_cache: Use cached results if available

        Returns:
            List of all available entities

        Raises:
            APIError: If API request fails

        Example:
            ```python
            entities = await client.list_apis()
            for entity in entities:
                print(f"{entity.api_scope}/{entity.api_url}")
            ```
        """
        # Return cached results if available and requested
        if use_cache and self._entities_cache is not None:
            return self._entities_cache

        # Get auth headers
        headers = await self._get_auth_headers()

        # Make API request
        response = await self.get("/api/v1/meta/apis", headers=headers)

        # Parse response
        data = response.json()
        api_response = DataResponse[list[dict[str, Any]]](**data)

        if not api_response.is_success():
            raise APIError(
                f"Failed to list APIs: {api_response.message}",
                status_code=api_response.status_code,
                response_data=data,
            )

        # Convert to EndpointEntity objects
        raw_data = api_response.get_data()
        endpoints_response = EndpointsResponse(entities=raw_data)

        # Cache results
        self._entities_cache = endpoints_response.entities

        return endpoints_response.entities

    async def list_apis_by_scope(
        self, scope: str, use_cache: bool = True
    ) -> list[EndpointEntity]:
        """
        List entities filtered by scope.

        Args:
            scope: API scope to filter by (e.g., "ops", "data", "metadata")
            use_cache: Use cached results if available

        Returns:
            List of entities in the specified scope

        Raises:
            APIError: If API request fails

        Example:
            ```python
            ops_entities = await client.list_apis_by_scope("ops")
            ```
        """
        entities = await self.list_apis(use_cache=use_cache)
        return [e for e in entities if e.api_scope == scope]

    async def get_api_info(
        self, api_url: str, use_cache: bool = True
    ) -> EndpointEntity:
        """
        Get information about a specific entity.

        Args:
            api_url: Entity URL (e.g., "ops/auditTrail")
            use_cache: Use cached results if available

        Returns:
            Entity information

        Raises:
            EntityNotFoundError: If entity is not found
            APIError: If API request fails

        Example:
            ```python
            entity = await client.get_api_info("ops/auditTrail")
            print(entity.description)
            ```
        """
        entities = await self.list_apis(use_cache=use_cache)

        # Search for matching entity
        for entity in entities:
            if entity.api_url == api_url:
                return entity

        raise EntityNotFoundError(f"Entity not found: {api_url}")

    def clear_apis_cache(self) -> None:
        """Clear cached entity list."""
        self._entities_cache = None

    # -------------------------------------------------------------------------
    # API #2: Metadata - Get field information
    # -------------------------------------------------------------------------

    async def get_metadata(self, api_url: str) -> list[FieldMetadata]:
        """
        Get metadata for an entity (API #2).

        Args:
            api_url: Entity URL (e.g., "ops/auditTrail")

        Returns:
            List of field metadata

        Raises:
            MetadataError: If metadata retrieval fails
            APIError: If API request fails

        Example:
            ```python
            metadata = await client.get_metadata("ops/auditTrail")
            for field in metadata:
                print(f"{field.field_name}: {field.type}")
            ```
        """
        # Parse api_url into scope and entity
        parts = api_url.split("/")
        if len(parts) != 2:
            raise MetadataError(
                f"Invalid api_url format: {api_url}. Expected 'scope/entity'"
            )

        scope, entity = parts

        # Get auth headers
        headers = await self._get_auth_headers()

        # Make API request
        path = f"/api/v1/meta/{scope}/{entity}"
        response = await self.get(path, headers=headers)

        # Parse response
        data = response.json()
        api_response = DataResponse[list[dict[str, Any]]](**data)

        if not api_response.is_success():
            raise MetadataError(
                f"Failed to get metadata for {api_url}: {api_response.message}",
                details={"api_url": api_url, "response": data},
            )

        # Convert to FieldMetadata objects
        raw_data = api_response.get_data()
        metadata_response = MetadataResponse(fields=raw_data)

        return metadata_response.fields

    async def get_primary_keys(self, api_url: str) -> list[str]:
        """
        Get primary key field names for an entity.

        Args:
            api_url: Entity URL (e.g., "ops/auditTrail")

        Returns:
            List of primary key field names

        Raises:
            MetadataError: If metadata retrieval fails

        Example:
            ```python
            pk_fields = await client.get_primary_keys("ops/auditTrail")
            print(f"Primary keys: {pk_fields}")
            ```
        """
        metadata = await self.get_metadata(api_url)
        return [field.field_name for field in metadata if field.is_primary_key]

    async def get_field_types(self, api_url: str) -> dict[str, str]:
        """
        Get field name to type mapping for an entity.

        Args:
            api_url: Entity URL (e.g., "ops/auditTrail")

        Returns:
            Dictionary mapping field names to types

        Raises:
            MetadataError: If metadata retrieval fails

        Example:
            ```python
            field_types = await client.get_field_types("ops/auditTrail")
            print(f"auditId type: {field_types['auditId']}")
            ```
        """
        metadata = await self.get_metadata(api_url)
        return {field.field_name: field.type for field in metadata}

    # -------------------------------------------------------------------------
    # API #3: Query - Retrieve entity data
    # -------------------------------------------------------------------------

    async def query(
        self,
        api_url: str,
        request: QueryRequest | None = None,
        timeout: float | None = None,
    ) -> QueryResponse:
        """
        Query entity data (API #3).

        Args:
            api_url: Entity URL (e.g., "ops/auditTrail")
            request: Query request with filters, sorting, pagination
            timeout: Optional timeout override for this request

        Returns:
            Query response with results

        Raises:
            QueryError: If query fails
            APIError: If API request fails

        Example:
            ```python
            # Simple query
            results = await client.query("ops/auditTrail")

            # With filters and pagination
            query = QueryRequest() \\
                .add_filter("tenantId", "=", 7) \\
                .add_filter("eventName", "LIKE", "CREATE%") \\
                .add_sort("auditId", "DESC") \\
                .limit(10)
            results = await client.query("ops/auditTrail", query)

            for row in results:
                print(row)
            ```
        """
        # Parse api_url into scope and entity
        parts = api_url.split("/")
        if len(parts) != 2:
            raise QueryError(
                f"Invalid api_url format: {api_url}. Expected 'scope/entity'"
            )

        scope, entity = parts

        # Use empty request if none provided
        if request is None:
            request = QueryRequest()

        # Get auth headers
        headers = await self._get_auth_headers()

        # Make API request
        path = f"/api/v1/{scope}/{entity}/query"
        response = await self.post(
            path,
            headers=headers,
            json=request.model_dump(by_alias=True, exclude_none=True),
            timeout=timeout,
        )

        # Parse response
        data = response.json()
        api_response = DataResponse[list[dict[str, Any]]](**data)

        if not api_response.is_success():
            raise QueryError(
                f"Query failed for {api_url}: {api_response.message}",
                details={"api_url": api_url, "request": request.model_dump(), "response": data},
            )

        # Convert to QueryResponse
        raw_data = api_response.get_data()
        return QueryResponse(data=raw_data)

    async def query_all(
        self, api_url: str, page_size: int = 1000, max_results: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Query all data from an entity with automatic pagination.

        Args:
            api_url: Entity URL (e.g., "ops/auditTrail")
            page_size: Number of records per page
            max_results: Optional maximum number of results to return

        Returns:
            List of all results

        Raises:
            QueryError: If query fails

        Example:
            ```python
            # Get all audit trail records
            all_records = await client.query_all("ops/auditTrail")

            # Get up to 5000 records
            records = await client.query_all("ops/auditTrail", max_results=5000)
            ```
        """
        all_results = []
        offset = 0

        while True:
            # Check if we've reached max_results
            if max_results and len(all_results) >= max_results:
                break

            # Calculate limit for this page
            limit = page_size
            if max_results:
                remaining = max_results - len(all_results)
                limit = min(limit, remaining)

            # Query this page
            request = QueryRequest(offset=offset, limit=limit)
            response = await self.query(api_url, request)

            # Add results
            page_results = list(response.results)
            if not page_results:
                break

            all_results.extend(page_results)

            # Check if we got fewer results than requested (last page)
            if len(page_results) < limit:
                break

            offset += limit

        return all_results

    async def query_with_filters(
        self, api_url: str, filters: list[tuple[str, str, Any]]
    ) -> QueryResponse:
        """
        Query entity with simple filter list.

        Args:
            api_url: Entity URL
            filters: List of (field, operation, value) tuples

        Returns:
            Query response with results

        Raises:
            QueryError: If query fails

        Example:
            ```python
            results = await client.query_with_filters(
                "ops/auditTrail",
                [
                    ("tenantId", "=", 7),
                    ("eventName", "LIKE", "CREATE%"),
                ]
            )
            ```
        """
        request = QueryRequest()
        for field, operation, value in filters:
            request.add_filter(field, operation, value)

        return await self.query(api_url, request)

    # -------------------------------------------------------------------------
    # Utility methods
    # -------------------------------------------------------------------------

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._auth_client.is_authenticated

    @property
    def current_user(self) -> Any | None:
        """Get current authenticated user data."""
        return self._auth_client.current_user

    @property
    def current_roles(self) -> tuple[str, ...]:
        """Get current user roles."""
        return self._auth_client.current_roles

    def logout(self) -> None:
        """Logout and clear cached tokens."""
        self._auth_client.logout()
