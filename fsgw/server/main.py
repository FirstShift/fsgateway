"""
FastAPI server for FSGW API exploration.

Provides a web-based interface for testing and exploring the FirstShift API Gateway.
"""

import os
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from fsgw import __version__
from fsgw.client import FSGWClient
from fsgw.models import QueryRequest

# Global client instance
client: FSGWClient | None = None


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
    title="FirstShift API Gateway Explorer",
    description="Web-based interface for exploring and testing the FirstShift API Gateway",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with server info."""
    return {
        "name": "FirstShift API Gateway Explorer",
        "version": __version__,
        "status": "running",
        "endpoints": {
            "list_endpoints": "GET /endpoints",
            "get_metadata": "GET /metadata/{entity}",
            "query_data": "POST /query/{entity}",
            "docs": "GET /docs",
        },
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/endpoints")
async def list_endpoints() -> dict[str, Any]:
    """
    List all available API endpoints (API #1).

    Returns all API groups and entities exposed by the platform.
    """
    client = get_client()
    response = await client.list_endpoints()

    if not response.success:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.error or "Failed to list endpoints",
        )

    return response.data.model_dump()


@app.get("/metadata/{entity}")
async def get_metadata(entity: str) -> dict[str, Any]:
    """
    Get metadata for a specific entity (API #2).

    Returns field-level schema information including data types,
    constraints, and primary keys.

    Args:
        entity: Entity name (e.g., "products", "customers")
    """
    client = get_client()
    response = await client.get_metadata(entity=entity)

    if not response.success:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.error or f"Failed to get metadata for {entity}",
        )

    return response.data.model_dump()


@app.post("/query/{entity}")
async def query_data(entity: str, request: QueryRequest) -> dict[str, Any]:
    """
    Query data for a specific entity (API #3).

    Supports fully generic querying with filters, sorting, pagination,
    and optional field projections.

    Args:
        entity: Entity name (e.g., "products", "customers")
        request: Query parameters including filters, sorting, pagination
    """
    client = get_client()
    response = await client.query(
        entity=entity,
        filters=request.filters,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
        page=request.page,
        limit=request.limit,
        fields=request.fields,
    )

    if not response.success:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.error or f"Failed to query {entity}",
        )

    return response.data.model_dump()


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
