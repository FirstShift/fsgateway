# fsgw - FirstShift API Gateway SDK

**Python SDK for FirstShift Metadata Query and Dynamic Entity Access API**

Version: 0.1.0 | Status: 🚧 In Development | Last Updated: 2025-11-15

---

## Overview

fsgw is a comprehensive Python SDK for interacting with FirstShift's new API Gateway. It provides a clean, Pythonic interface to dynamically discover, introspect, and query any entity exposed by the platform with full async support, type safety, and lazy authentication.

### Key Features

- 🔄 **Async-First Design**: Built on `httpx` with full async/await support
- 🎯 **Type-Safe**: Complete type hints with Pydantic v2 models
- 🔐 **Lazy Authentication**: Automatic token-based auth (reuses shiftfm auth)
- 🔍 **Dynamic Discovery**: List all available API groups and entities
- 📊 **Metadata Introspection**: Get field-level schema for any entity
- 🔎 **Generic Querying**: Query any entity with filters, sorting, and pagination
- 🛠️ **CLI Tool**: Interactive command-line interface for API exploration
- 🌐 **FastAPI Server**: Web-based API explorer and testing interface
- 🐍 **Python 3.12+**: Modern Python with latest language features
- 📚 **Comprehensive Documentation**: API reference, guides, and examples

---

## Quick Start

### Installation

```bash
# Install via uv (recommended)
uv sync

# Or via pip
pip install -e .
```

### Basic Usage

```python
from fsgw.client import FSGWClient

# Initialize client - authentication happens automatically on first API call
async with FSGWClient(
    gateway_url="https://dev-cloudgateway.firstshift.ai",
    tenant_id=7,
    username="your-username",
    password="your-password"
) as client:
    # API #1 - List all available endpoints
    endpoints = await client.list_endpoints()
    if endpoints.success:
        for group in endpoints.data.groups:
            print(f"Group: {group.name}")
            for entity in group.entities:
                print(f"  - {entity.name}: {entity.endpoint}")

    # API #2 - Get metadata for an entity
    metadata = await client.get_metadata(entity="products")
    if metadata.success:
        for field in metadata.data.fields:
            print(f"{field.name}: {field.data_type} (PK: {field.is_primary_key})")

    # API #3 - Query data with filters
    results = await client.query(
        entity="products",
        filters={"category": "electronics"},
        sort_by="price",
        limit=10
    )
    if results.success:
        for item in results.data.items:
            print(item)
```

### CLI Usage

```bash
# List all available endpoints
fsgw endpoints list

# Get metadata for an entity
fsgw metadata get products

# Query data from an entity
fsgw query products --filter "category=electronics" --limit 10

# Interactive mode
fsgw interactive
```

### Web Server

```bash
# Start FastAPI server
fsgw-server

# Or with custom settings
fsgw-server --host 0.0.0.0 --port 8000 --reload
```

Then visit http://localhost:8000/docs for the interactive API documentation.

---

## Architecture

### Directory Structure

```
fsgw/
├── __init__.py
├── auth/                       # Authentication (from shiftfm)
│   ├── __init__.py
│   ├── models.py              # Auth models
│   └── sdk.py                 # Auth SDK
│
├── client/                     # HTTP client and framework
│   ├── __init__.py
│   ├── client.py              # Main FSGWClient
│   ├── decorators.py          # API method decorators
│   └── models.py              # HTTP models and errors
│
├── api/                        # API implementations
│   ├── __init__.py
│   ├── endpoints.py           # API #1 - List endpoints
│   ├── metadata.py            # API #2 - Get metadata
│   └── query.py               # API #3 - Query data
│
├── models/                     # Data models
│   ├── __init__.py
│   ├── endpoints.py           # Endpoint discovery models
│   ├── metadata.py            # Metadata models
│   └── query.py               # Query request/response models
│
├── cli/                        # Command-line interface
│   ├── __init__.py
│   ├── main.py                # CLI entry point
│   ├── endpoints.py           # Endpoints commands
│   ├── metadata.py            # Metadata commands
│   └── query.py               # Query commands
│
└── server/                     # FastAPI server
    ├── __init__.py
    ├── main.py                # Server entry point
    ├── routes.py              # API routes
    └── models.py              # Server-specific models
```

---

## API Methods

### API #1 - List All Available Endpoints

Dynamically discover all API groups and entities exposed by the platform.

```python
# List all endpoints
endpoints = await client.list_endpoints()

# Access endpoint information
for group in endpoints.data.groups:
    print(f"Group: {group.name}")
    for entity in group.entities:
        print(f"  Entity: {entity.name}")
        print(f"  Endpoint: {entity.endpoint}")
        print(f"  Methods: {entity.methods}")
```

### API #2 - Get Metadata for Any Entity

Returns field-level schema information including data types, constraints, and primary keys.

```python
# Get metadata for an entity
metadata = await client.get_metadata(entity="products")

# Access field information
for field in metadata.data.fields:
    print(f"Field: {field.name}")
    print(f"  Type: {field.data_type}")
    print(f"  Required: {field.required}")
    print(f"  Primary Key: {field.is_primary_key}")
    print(f"  Nullable: {field.nullable}")
    if field.constraints:
        print(f"  Constraints: {field.constraints}")
```

### API #3 - Query Data for Any Entity

Supports fully generic querying with filters, sorting, pagination, and optional projections.

```python
# Basic query
results = await client.query(entity="products")

# Query with filters
results = await client.query(
    entity="products",
    filters={
        "category": "electronics",
        "price": {"$gt": 100, "$lt": 1000}
    }
)

# Query with sorting and pagination
results = await client.query(
    entity="products",
    filters={"status": "active"},
    sort_by="price",
    sort_order="desc",
    page=1,
    limit=20
)

# Query with field projection
results = await client.query(
    entity="products",
    fields=["id", "name", "price", "category"],
    filters={"status": "active"}
)

# Access results
for item in results.data.items:
    print(item)

# Pagination info
print(f"Total: {results.data.total}")
print(f"Page: {results.data.page}")
print(f"Pages: {results.data.total_pages}")
```

---

## Authentication

fsgw reuses the authentication mechanism from shiftfm (FirstShift FM SDK), providing seamless integration across FirstShift APIs.

### Lazy Authentication (Recommended)

```python
from fsgw.client import FSGWClient

# Simply provide credentials - authentication happens automatically
async with FSGWClient(
    gateway_url="https://dev-cloudgateway.firstshift.ai",
    tenant_id=7,
    username="your-username",
    password="your-password"
) as client:
    # First API call triggers authentication automatically
    endpoints = await client.list_endpoints()
```

---

## CLI Reference

### Global Options

```bash
fsgw --help                    # Show help
fsgw --version                 # Show version
fsgw --config FILE             # Use config file
```

### Endpoints Commands

```bash
fsgw endpoints list            # List all available endpoints
fsgw endpoints show GROUP      # Show entities in a group
```

### Metadata Commands

```bash
fsgw metadata get ENTITY       # Get metadata for entity
fsgw metadata show ENTITY      # Pretty-print metadata
fsgw metadata fields ENTITY    # List fields only
```

### Query Commands

```bash
fsgw query ENTITY              # Query all records
fsgw query ENTITY --filter "field=value"
fsgw query ENTITY --filter "field1=value1" --filter "field2=value2"
fsgw query ENTITY --sort-by FIELD
fsgw query ENTITY --sort-by FIELD --sort-order desc
fsgw query ENTITY --limit 10 --page 2
fsgw query ENTITY --fields id,name,price
fsgw query ENTITY --output json
fsgw query ENTITY --output table
fsgw query ENTITY --output csv
```

### Interactive Mode

```bash
fsgw interactive              # Start interactive shell
```

---

## FastAPI Server

The included FastAPI server provides a web-based interface for exploring and testing the API Gateway.

### Starting the Server

```bash
# Start with defaults (http://localhost:8000)
fsgw-server

# Custom host and port
fsgw-server --host 0.0.0.0 --port 8080

# With auto-reload for development
fsgw-server --reload
```

### Available Endpoints

- `GET /` - Server info and status
- `GET /endpoints` - List all available endpoints (API #1)
- `GET /metadata/{entity}` - Get metadata for entity (API #2)
- `POST /query/{entity}` - Query entity data (API #3)
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Example Server Usage

```bash
# List endpoints
curl http://localhost:8000/endpoints

# Get metadata
curl http://localhost:8000/metadata/products

# Query data
curl -X POST http://localhost:8000/query/products \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {"category": "electronics"},
    "limit": 10
  }'
```

---

## Development

### Project Setup

```bash
# Clone repository
cd /Users/al/Projects/firstshift/fsgateway

# Install dependencies
uv sync

# Run quality checks
uv run ruff check fsgw/
uv run ruff format fsgw/
uv run mypy fsgw/

# Run tests
uv run pytest tests/ -v
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=fsgw --cov-report=html --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_client.py -v

# Run specific test
uv run pytest tests/test_client.py::test_list_endpoints -v
```

---

## Relationship to shiftfm

fsgw is designed to complement shiftfm (FirstShift FM SDK):

```
┌─────────────────┐     ┌──────────────┐
│  shiftfm SDK    │     │  fsgw SDK    │
│  (FM APIs)      │     │  (Gateway)   │
├─────────────────┤     ├──────────────┤
│ • Forecasting   │     │ • Discovery  │
│ • Planning      │     │ • Metadata   │
│ • Workbench     │     │ • Queries    │
│ • Auth          │ ←──→│ • Dynamic    │
└─────────────────┘     └──────────────┘
        │                       │
        └───────────┬───────────┘
                    │
            ┌───────▼────────┐
            │  FirstShift    │
            │  Platform      │
            └────────────────┘
```

- **shiftfm**: Domain-specific SDK for forecasting, planning, and workbench operations
- **fsgw**: Generic SDK for dynamic discovery and querying of any entity
- **Shared Authentication**: Both use the same auth mechanism

---

## Documentation

### API Documentation

See [docs/FirstShift_Metadata_Query_API_Doc.docx](docs/FirstShift_Metadata_Query_API_Doc.docx) for the complete API specification.

### Related Projects

- **shiftfm**: [../forecast_agent/vibescm/shiftfm/](../forecast_agent/vibescm/shiftfm/)
- **vibeSCM**: [../forecast_agent/vibescm/](../forecast_agent/vibescm/)

---

## License

Proprietary - FirstShift AI

Internal project - not for public distribution.

---

## Support

For issues, questions, or feature requests:

- **Documentation**: Check `docs/` for guides and reference
- **Examples**: Review `tests/` for usage patterns
- **Issues**: Create GitHub issue with reproduction steps

---

**Built with ❤️ by FirstShift AI**

Part of the FirstShift platform - Modernizing supply chain management with AI-powered workspaces.
