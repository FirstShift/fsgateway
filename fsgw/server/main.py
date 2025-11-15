"""
FirstShift Gateway Documentation Server.

Interactive web documentation for exploring all FirstShift API endpoints,
metadata, and usage examples. Auto-discovers all entities from the gateway.
"""

import os
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from fsgw import __version__
from fsgw.client import FSGWClient
from fsgw.models import EndpointEntity, FieldMetadata, QueryRequest

# Global state
client: FSGWClient | None = None
_entities_cache: list[EndpointEntity] = []
_metadata_cache: dict[str, list[FieldMetadata]] = {}


def get_client() -> FSGWClient:
    """Get or create client instance."""
    global client

    if client is None:
        gateway_url = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
        tenant_id = int(os.getenv("FSGW_TENANT_ID", "7"))
        username = os.getenv("FSGW_USERNAME", "")
        password = os.getenv("FSGW_PASSWORD", "")

        if not username or not password:
            raise RuntimeError("FSGW_USERNAME and FSGW_PASSWORD must be set")

        client = FSGWClient(
            gateway_url=gateway_url,
            tenant_id=tenant_id,
            username=username,
            password=password,
        )

    return client


async def discover_entities() -> list[EndpointEntity]:
    """Discover all entities from gateway."""
    global _entities_cache

    if not _entities_cache:
        client_inst = get_client()
        _entities_cache = await client_inst.list_apis(use_cache=False)

    return _entities_cache


# Response models
class EntitySummary(BaseModel):
    """Summary of an entity."""
    api_scope: str
    api_url: str
    external_api_name: str
    description: str | None
    metadata_url: str
    query_url: str


class ScopeGroup(BaseModel):
    """Group of entities by scope."""
    scope: str
    count: int
    entities: list[EntitySummary]


class DiscoveryResponse(BaseModel):
    """Discovery response with all entities."""
    total_entities: int
    scopes: list[str]
    groups: list[ScopeGroup]


class FieldInfo(BaseModel):
    """Field information."""
    field_name: str
    type: str
    is_primary_key: bool
    is_nullable: bool


class MetadataResponse(BaseModel):
    """Metadata response for an entity."""
    entity: str
    total_fields: int
    primary_keys: list[str]
    fields: list[FieldInfo]


class QueryExample(BaseModel):
    """Example query."""
    title: str
    description: str
    request: dict[str, Any]
    curl_example: str


class QueryDocsResponse(BaseModel):
    """Query documentation for an entity."""
    entity: str
    query_endpoint: str
    examples: list[QueryExample]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI."""
    # Startup
    yield
    # Shutdown
    global client
    if client:
        await client.close()


# Create FastAPI app
app = FastAPI(
    title="FirstShift Gateway API Documentation",
    description="""
    Interactive documentation for FirstShift Gateway APIs.

    This server auto-discovers all available API endpoints from the FirstShift Gateway
    and provides comprehensive documentation including:
    - Entity discovery and browsing (239+ entities)
    - Field metadata and schema information
    - Query examples and testing
    - Live API status and health checks
    """,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with navigation."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FirstShift Gateway API Documentation</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2563eb;
                border-bottom: 3px solid #2563eb;
                padding-bottom: 10px;
            }
            h2 {
                color: #1e40af;
                margin-top: 30px;
            }
            .card {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }
            .endpoint {
                background: #dbeafe;
                padding: 10px 15px;
                border-radius: 6px;
                margin: 10px 0;
                font-family: monospace;
            }
            a {
                color: #2563eb;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .feature {
                margin: 15px 0;
                padding-left: 20px;
            }
            .feature::before {
                content: "✓ ";
                color: #10b981;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1>FirstShift Gateway API Documentation</h1>

        <div class="card">
            <h2>Welcome</h2>
            <p>
                This is an interactive documentation server for exploring all FirstShift Gateway APIs.
                The system auto-discovers all available entities and provides comprehensive metadata
                and usage examples.
            </p>
        </div>

        <div class="card">
            <h2>Features</h2>
            <div class="feature">Browse all 239+ entities organized by scope</div>
            <div class="feature">View detailed field metadata and schema information</div>
            <div class="feature">Interactive query examples and testing</div>
            <div class="feature">Live API health and status monitoring</div>
            <div class="feature">Auto-generated OpenAPI/Swagger documentation</div>
        </div>

        <div class="card">
            <h2>Quick Links</h2>
            <div class="endpoint">
                <a href="/entities">GET /entities</a> - Browse all entities
            </div>
            <div class="endpoint">
                <a href="/entities/ops">GET /entities/{scope}</a> - Filter by scope
            </div>
            <div class="endpoint">
                <a href="/entities/ops/auditTrail/metadata">GET /entities/{scope}/{entity}/metadata</a> - View metadata
            </div>
            <div class="endpoint">
                <a href="/search?q=audit">GET /search?q={term}</a> - Search entities
            </div>
            <div class="endpoint">
                <a href="/health">GET /health</a> - API health check
            </div>
        </div>

        <div class="card">
            <h2>Interactive Documentation</h2>
            <p>
                For full interactive API testing with OpenAPI/Swagger:
            </p>
            <div class="endpoint">
                <a href="/docs">Swagger UI Documentation</a>
            </div>
            <div class="endpoint">
                <a href="/redoc">ReDoc Documentation</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        client_inst = get_client()
        entities = await discover_entities()

        return {
            "status": "healthy",
            "authenticated": client_inst.is_authenticated,
            "total_entities": len(entities),
            "gateway_url": os.getenv("FSGW_GATEWAY_URL"),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@app.get("/entities", response_model=DiscoveryResponse)
async def list_entities():
    """
    List all available API entities grouped by scope.

    Returns comprehensive information about all 239+ entities available
    in the FirstShift Gateway.
    """
    entities = await discover_entities()

    # Group by scope
    by_scope: dict[str, list[EndpointEntity]] = defaultdict(list)
    for entity in entities:
        by_scope[entity.api_scope].append(entity)

    # Build response
    groups = []
    for scope in sorted(by_scope.keys()):
        scope_entities = by_scope[scope]
        groups.append(
            ScopeGroup(
                scope=scope,
                count=len(scope_entities),
                entities=[
                    EntitySummary(
                        api_scope=e.api_scope,
                        api_url=e.api_url,
                        external_api_name=e.external_api_name,
                        description=e.description,
                        metadata_url=f"/entities/{e.api_url}/metadata",
                        query_url=f"/entities/{e.api_url}/query",
                    )
                    for e in sorted(scope_entities, key=lambda x: x.api_url)
                ],
            )
        )

    return DiscoveryResponse(
        total_entities=len(entities),
        scopes=list(by_scope.keys()),
        groups=groups,
    )


@app.get("/entities/{scope}", response_model=list[EntitySummary])
async def list_entities_by_scope(scope: str):
    """
    List entities filtered by scope.

    **Available scopes:**
    - `config` - Configuration entities
    - `data` - Data entities
    - `globalmeta` - Global metadata
    - `metadata` - Metadata entities
    - `ops` - Operations entities
    - `rbac` - Role-based access control
    """
    client_inst = get_client()
    entities = await client_inst.list_apis_by_scope(scope)

    if not entities:
        raise HTTPException(status_code=404, detail=f"No entities found for scope: {scope}")

    return [
        EntitySummary(
            api_scope=e.api_scope,
            api_url=e.api_url,
            external_api_name=e.external_api_name,
            description=e.description,
            metadata_url=f"/entities/{e.api_url}/metadata",
            query_url=f"/entities/{e.api_url}/query",
        )
        for e in entities
    ]


@app.get("/entities/{scope}/{entity}/metadata", response_model=MetadataResponse)
async def get_entity_metadata(scope: str, entity: str):
    """
    Get detailed metadata for a specific entity.

    Returns comprehensive field information including:
    - Field names and data types
    - Primary key fields
    - Nullable constraints

    **Example:**
    ```
    GET /entities/ops/auditTrail/metadata
    ```
    """
    api_url = f"{scope}/{entity}"

    # Check cache
    global _metadata_cache
    if api_url not in _metadata_cache:
        client_inst = get_client()
        try:
            metadata = await client_inst.get_metadata(api_url)
            _metadata_cache[api_url] = metadata
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Entity not found or metadata unavailable: {api_url}. Error: {str(e)}",
            )

    metadata = _metadata_cache[api_url]
    primary_keys = [f.field_name for f in metadata if f.is_primary_key]

    return MetadataResponse(
        entity=api_url,
        total_fields=len(metadata),
        primary_keys=primary_keys,
        fields=[
            FieldInfo(
                field_name=f.field_name,
                type=f.type,
                is_primary_key=f.is_primary_key,
                is_nullable=f.field_can_be_null,
            )
            for f in metadata
        ],
    )


@app.get("/entities/{scope}/{entity}/query", response_model=QueryDocsResponse)
async def get_query_docs(scope: str, entity: str):
    """
    Get query documentation and examples for an entity.

    Returns example queries with curl commands that can be copy-pasted
    for testing.

    **Example:**
    ```
    GET /entities/ops/auditTrail/query
    ```
    """
    api_url = f"{scope}/{entity}"

    # Verify entity exists
    client_inst = get_client()
    try:
        await client_inst.get_api_info(api_url)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Entity not found: {api_url}")

    # Get metadata for field names
    try:
        metadata = await client_inst.get_metadata(api_url)
        field_names = [f.field_name for f in metadata[:5]]  # First 5 fields
    except Exception:
        field_names = []

    gateway_url = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")

    examples = [
        QueryExample(
            title="Simple Query",
            description="Retrieve first 10 records",
            request={
                "criteriaList": [],
                "orderByList": [],
                "selectFieldsList": [],
                "offset": 0,
                "limit": 10,
            },
            curl_example=f"""curl -X POST "{gateway_url}/api/v1/{scope}/{entity}/query" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"limit": 10}}'""",
        ),
        QueryExample(
            title="Query with Field Selection",
            description="Select specific fields only",
            request={
                "criteriaList": [],
                "orderByList": [],
                "selectFieldsList": field_names,
                "offset": 0,
                "limit": 10,
            },
            curl_example=f"""curl -X POST "{gateway_url}/api/v1/{scope}/{entity}/query" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"selectFieldsList": {field_names}, "limit": 10}}'""",
        ),
    ]

    return QueryDocsResponse(
        entity=api_url,
        query_endpoint=f"{gateway_url}/api/v1/{scope}/{entity}/query",
        examples=examples,
    )


@app.get("/search")
async def search_entities(q: str = Query(..., description="Search term")):
    """
    Search entities by name, scope, or description.

    **Example:**
    ```
    GET /search?q=audit
    ```
    """
    entities = await discover_entities()

    q_lower = q.lower()
    results = [
        EntitySummary(
            api_scope=e.api_scope,
            api_url=e.api_url,
            external_api_name=e.external_api_name,
            description=e.description,
            metadata_url=f"/entities/{e.api_url}/metadata",
            query_url=f"/entities/{e.api_url}/query",
        )
        for e in entities
        if (
            q_lower in e.api_url.lower()
            or q_lower in e.external_api_name.lower()
            or (e.description and q_lower in e.description.lower())
        )
    ]

    return {
        "query": q,
        "total_results": len(results),
        "results": results,
    }


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc: RuntimeError):
    """Handle runtime errors (e.g., missing credentials)."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


def main(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """
    Start the FastAPI server.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
    """
    uvicorn.run(
        "fsgw.server.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    import sys

    # Simple CLI argument parsing
    host = "0.0.0.0"
    port = 8000
    reload = "--reload" in sys.argv

    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        if idx + 1 < len(sys.argv):
            host = sys.argv[idx + 1]

    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    main(host=host, port=port, reload=reload)
