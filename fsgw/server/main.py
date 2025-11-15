"""
FirstShift Gateway Documentation Server.

Interactive web documentation for exploring all FirstShift API endpoints,
metadata, and usage examples. Auto-discovers all entities from the gateway.
"""

import os
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from fsgw import __version__
from fsgw.client import FSGWClient
from fsgw.models import EndpointEntity, FieldMetadata, QueryRequest

# Load .env file if it exists
env_path = Path.cwd() / ".env"
if env_path.exists():
    load_dotenv(env_path)

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

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"
templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Landing page - Home."""
    entities = await discover_entities()

    # Group by scope
    by_scope: dict[str, list[EndpointEntity]] = defaultdict(list)
    for entity in entities:
        by_scope[entity.api_scope].append(entity)

    # Calculate stats
    total_fields = 0
    for scope_entities in by_scope.values():
        for entity in scope_entities[:10]:  # Sample first 10 per scope
            try:
                metadata = await get_client().get_metadata(entity.api_url)
                total_fields += len(metadata)
            except:
                pass

    scopes_data = {
        scope: {
            "count": len(entities_list),
            "description": f"{scope.capitalize()} scope entities"
        }
        for scope, entities_list in by_scope.items()
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_entities": len(entities),
        "total_scopes": len(by_scope),
        "total_fields": total_fields,
        "scopes": scopes_data,
        "featured_entities": entities[:10]  # First 10 entities as featured
    })


@app.get("/docs/entities", response_class=HTMLResponse)
async def docs_entities_page(request: Request):
    """HTML page: Browse all entities."""
    entities = await discover_entities()

    # Group by scope
    by_scope: dict[str, list[EndpointEntity]] = defaultdict(list)
    for entity in entities:
        by_scope[entity.api_scope].append(entity)

    scopes_data = {
        scope: {"count": len(entities_list)}
        for scope, entities_list in by_scope.items()
    }

    return templates.TemplateResponse("entities.html", {
        "request": request,
        "entities": sorted(entities, key=lambda e: e.api_url),
        "scopes": scopes_data,
        "current_scope": None
    })


@app.get("/docs/scope/{scope}", response_class=HTMLResponse)
async def docs_scope_page(request: Request, scope: str):
    """HTML page: Entities filtered by scope."""
    client_inst = get_client()
    entities = await client_inst.list_apis_by_scope(scope)

    if not entities:
        raise HTTPException(status_code=404, detail=f"No entities found for scope: {scope}")

    # Get all scopes for sidebar
    all_entities = await discover_entities()
    by_scope: dict[str, list[EndpointEntity]] = defaultdict(list)
    for entity in all_entities:
        by_scope[entity.api_scope].append(entity)

    scopes_data = {
        s: {"count": len(e_list)}
        for s, e_list in by_scope.items()
    }

    return templates.TemplateResponse("entities.html", {
        "request": request,
        "entities": sorted(entities, key=lambda e: e.api_url),
        "scopes": scopes_data,
        "current_scope": scope
    })


@app.get("/docs/entity/{scope}/{entity}", response_class=HTMLResponse)
async def docs_entity_page(request: Request, scope: str, entity: str):
    """HTML page: Entity detail page."""
    api_url = f"{scope}/{entity}"
    client_inst = get_client()

    # Get entity info
    try:
        entity_info = await client_inst.get_api_info(api_url)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Entity not found: {api_url}")

    # Get metadata
    try:
        metadata = await client_inst.get_metadata(api_url)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Metadata unavailable for {api_url}: {str(e)}"
        )

    primary_keys = [f.field_name for f in metadata if f.is_primary_key]

    return templates.TemplateResponse("entity_detail.html", {
        "request": request,
        "entity": entity_info,
        "metadata": metadata,
        "primary_keys": primary_keys
    })


@app.get("/docs/api", response_class=HTMLResponse)
async def docs_api_page(request: Request):
    """HTML page: API reference documentation."""
    return templates.TemplateResponse("api_reference.html", {
        "request": request
    })


# ============================================================================
# JSON API Endpoints (programmatic access)
# ============================================================================

@app.get("/api/health")
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


@app.get("/api/entities", response_model=DiscoveryResponse)
async def list_entities():
    """
    JSON API: List all available API entities grouped by scope.

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
                        metadata_url=f"/api/entities/{e.api_url}/metadata",
                        query_url=f"/api/entities/{e.api_url}/query",
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


@app.get("/api/entities/{scope}", response_model=list[EntitySummary])
async def list_entities_by_scope(scope: str):
    """
    JSON API: List entities filtered by scope.

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
            metadata_url=f"/api/entities/{e.api_url}/metadata",
            query_url=f"/api/entities/{e.api_url}/query",
        )
        for e in entities
    ]


@app.get("/api/entities/{scope}/{entity}/metadata", response_model=MetadataResponse)
async def get_entity_metadata(scope: str, entity: str):
    """
    JSON API: Get detailed metadata for a specific entity.

    Returns comprehensive field information including:
    - Field names and data types
    - Primary key fields
    - Nullable constraints

    **Example:**
    ```
    GET /api/entities/ops/auditTrail/metadata
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


@app.get("/api/entities/{scope}/{entity}/query", response_model=QueryDocsResponse)
async def get_query_docs(scope: str, entity: str):
    """
    JSON API: Get query documentation and examples for an entity.

    Returns example queries with curl commands that can be copy-pasted
    for testing.

    **Example:**
    ```
    GET /api/entities/ops/auditTrail/query
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
  -H "access-token: YOUR_TOKEN" \\
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
  -H "access-token: YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"selectFieldsList": {field_names}, "limit": 10}}'""",
        ),
    ]

    return QueryDocsResponse(
        entity=api_url,
        query_endpoint=f"{gateway_url}/api/v1/{scope}/{entity}/query",
        examples=examples,
    )


@app.get("/api/search")
async def search_entities(q: str = Query(..., description="Search term")):
    """
    JSON API: Search entities by name, scope, or description.

    **Example:**
    ```
    GET /api/search?q=audit
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
            metadata_url=f"/api/entities/{e.api_url}/metadata",
            query_url=f"/api/entities/{e.api_url}/query",
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
    # Support PORT env var for hosting services (Render, Railway, etc.)
    port = int(os.getenv("PORT", "8000"))
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
