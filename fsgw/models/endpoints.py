"""
Models for API #1 - List All Available Endpoints.

Used to dynamically discover all API entities exposed by the platform.
"""

from pydantic import BaseModel, Field


class EndpointEntity(BaseModel):
    """
    A single entity exposed by the API.

    Represents a queryable data entity from the FirstShift Gateway.
    Matches the actual API response structure from /api/v1/meta/apis
    """

    api_scope: str = Field(
        ...,
        alias="apiScope",
        description="Entity scope/category (config, data, metadata, ops, rbac, globalmeta)",
    )
    api_url: str = Field(
        ...,
        alias="apiUrl",
        description="API path for this entity (e.g., 'ops/auditTrail', 'config/configDataEntities')",
    )
    external_api_name: str = Field(
        ...,
        alias="externalAPIName",
        description="External/friendly name for the entity",
    )
    description: str | None = Field(
        default=None, description="Description of what this entity contains"
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True

    def to_path_components(self) -> tuple[str, str]:
        """
        Split apiUrl into scope and entity name.

        Returns:
            Tuple of (scope, entity_name)

        Examples:
            "ops/auditTrail" -> ("ops", "auditTrail")
            "config/configDataEntities" -> ("config", "configDataEntities")
        """
        parts = self.api_url.split("/", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], parts[0]

    @property
    def scope(self) -> str:
        """Get the scope part of the apiUrl."""
        return self.to_path_components()[0]

    @property
    def entity_name(self) -> str:
        """Get the entity name part of the apiUrl."""
        return self.to_path_components()[1]

    def get_metadata_url(self) -> str:
        """
        Get the URL path for fetching this entity's metadata (API #2).

        Returns:
            URL path like "/api/v1/meta/ops/auditTrail"
        """
        scope, entity = self.to_path_components()
        return f"/api/v1/meta/{scope}/{entity}"

    def get_query_url(self) -> str:
        """
        Get the URL path for querying this entity's data (API #3).

        Returns:
            URL path like "/api/v1/ops/auditTrail/query"
        """
        scope, entity = self.to_path_components()
        return f"/api/v1/{scope}/{entity}/query"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump(by_alias=True)


class EndpointGroup(BaseModel):
    """
    A logical grouping of entities by scope.

    Groups organize entities by their apiScope.
    """

    scope: str = Field(description="Scope name (config, data, metadata, ops, rbac, globalmeta)")
    entities: list[EndpointEntity] = Field(
        default_factory=list, description="Entities in this scope"
    )

    @property
    def count(self) -> int:
        """Get number of entities in this group."""
        return len(self.entities)


class EndpointsResponse(BaseModel):
    """
    Response from API #1 - List All Available Endpoints.

    Contains all entities grouped by scope.
    """

    entities: list[EndpointEntity] = Field(
        default_factory=list, description="All available entities"
    )

    def group_by_scope(self) -> dict[str, EndpointGroup]:
        """
        Group entities by their scope.

        Returns:
            Dictionary mapping scope name to EndpointGroup
        """
        groups: dict[str, list[EndpointEntity]] = {}

        for entity in self.entities:
            scope = entity.api_scope
            if scope not in groups:
                groups[scope] = []
            groups[scope].append(entity)

        return {
            scope: EndpointGroup(scope=scope, entities=entities)
            for scope, entities in groups.items()
        }

    def get_by_scope(self, scope: str) -> list[EndpointEntity]:
        """
        Get all entities for a specific scope.

        Args:
            scope: Scope name (config, data, metadata, ops, rbac, globalmeta)

        Returns:
            List of entities in that scope
        """
        return [e for e in self.entities if e.api_scope == scope]

    def get_by_url(self, api_url: str) -> EndpointEntity | None:
        """
        Find entity by its apiUrl.

        Args:
            api_url: API URL path (e.g., "ops/auditTrail")

        Returns:
            EndpointEntity or None if not found
        """
        for entity in self.entities:
            if entity.api_url == api_url:
                return entity
        return None

    def search(self, query: str) -> list[EndpointEntity]:
        """
        Search entities by name or description.

        Args:
            query: Search query string

        Returns:
            List of matching entities
        """
        query_lower = query.lower()
        results = []

        for entity in self.entities:
            if (
                query_lower in entity.external_api_name.lower()
                or query_lower in entity.api_url.lower()
                or (entity.description and query_lower in entity.description.lower())
            ):
                results.append(entity)

        return results

    @property
    def total_entities(self) -> int:
        """Get total number of entities."""
        return len(self.entities)

    @property
    def scopes(self) -> list[str]:
        """Get list of all scopes."""
        return sorted(set(e.api_scope for e in self.entities))
