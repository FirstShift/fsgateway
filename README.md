# FirstShift Gateway SDK (FSGW)

Python SDK and interactive documentation for the FirstShift Gateway API.

**Version**: 0.1.0 | **Status**: 🚧 In Development | **Last Updated**: 2025-11-15

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repo-url>
cd fsgateway

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### 2. Configuration

Create a `.env` file with your credentials:

```bash
FSGW_GATEWAY_URL=https://dev-cloudgateway.firstshift.ai
FSGW_TENANT_ID=7
FSGW_USERNAME=your_username
FSGW_PASSWORD=your_password
```

### 3. Choose Your Interface

**Python SDK:**
```python
from fsgw.client import FSGWClient

async with FSGWClient(...) as client:
    entities = await client.list_apis()
    metadata = await client.get_metadata("ops/auditTrail")
    results = await client.query("ops/auditTrail")
```

**Interactive CLI:**
```bash
uv run fsgw interactive
```

**Documentation Server:**
```bash
uv run fsgw server
# Visit http://localhost:8000
```

## Features

### 🐍 Python SDK
- Async-first design with `httpx`
- Type-safe with Pydantic v2
- Auto-authentication and token refresh
- Query builder with filters, sorting, pagination
- 239+ FirstShift entities

### 🌐 Documentation Website
- Interactive web documentation
- Searchable entity browser
- Detailed field metadata
- Query examples (Python, REST, CLI)
- Beautiful, modern UI

### 🖥️ CLI Tools
- Interactive REPL mode
- Natural language queries
- Entity browsing and search
- Metadata inspection

## Documentation

| Document | Description |
|----------|-------------|
| **[QUICKSTART.md](QUICKSTART.md)** | Complete usage guide with examples |
| **[docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md)** | Current project status and progress |
| **[docs/phases/SDK_DEVELOPMENT_CHECKLIST.md](docs/phases/SDK_DEVELOPMENT_CHECKLIST.md)** | Development checklist and roadmap |
| **[deployment/SETUP_GUIDE.md](deployment/SETUP_GUIDE.md)** | Deploy docs to remote server |
| **[deployment/ARCHITECTURE.md](deployment/ARCHITECTURE.md)** | System architecture and diagrams |
| [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md) | Advanced deployment options |

## Project Structure

```
fsgateway/
├── fsgw/                          # Main Python package
│   ├── client/                    # HTTP client & auth
│   ├── models/                    # Pydantic models
│   ├── cli/                       # CLI commands
│   └── server/                    # Documentation server
│       ├── main.py                # FastAPI application
│       ├── templates/             # HTML templates
│       └── static/                # CSS, JS assets
├── deployment/                    # Deployment files
│   ├── setup_deployment.sh        # Setup & test connection
│   ├── deploy.sh                  # Manual deployment
│   ├── SETUP_GUIDE.md             # Deployment guide
│   ├── ARCHITECTURE.md            # Architecture docs
│   └── DEPLOYMENT.md              # Advanced docs
├── docs/                          # Documentation
│   ├── CURRENT_STATUS.md          # Current project status
│   ├── phases/                    # Development phases
│   └── guides/                    # User guides
├── tests/                         # Test suite
├── .env.example                   # Example configuration
├── pyproject.toml                 # Project metadata
├── QUICKSTART.md                  # Quick start guide
└── README.md                      # This file
```

## CLI Usage

```bash
# Interactive REPL
uv run fsgw interactive

# Browse entities
uv run fsgw entities

# Search entities
uv run fsgw search "audit"

# Get entity info
uv run fsgw info ops/auditTrail

# Query data
uv run fsgw query ops/auditTrail

# Start documentation server
uv run fsgw server
```

## Python SDK Examples

```python
from fsgw.client import FSGWClient
from fsgw.models.query import QueryRequest

async with FSGWClient(
    gateway_url="https://dev-cloudgateway.firstshift.ai",
    username="your_username",
    password="your_password",
    tenant_id=7,
) as client:
    # Discover entities
    entities = await client.list_apis()
    ops_entities = await client.list_apis_by_scope("ops")

    # Get metadata
    metadata = await client.get_metadata("ops/auditTrail")

    # Build and execute queries
    query = QueryRequest() \
        .add_filter("tenantId", "=", 7) \
        .order_by("createdAt", desc=True) \
        .limit(100)

    results = await client.query("ops/auditTrail", query)
```

## Deploy Documentation Website

Deploy the interactive documentation to your remote server:

```bash
# 1. Setup and test connection
./deployment/setup_deployment.sh

# 2. Deploy to VM
./deployment/deploy_remote.sh

# 3. Access via SSH tunnel
ssh -L 8100:localhost:8100 user@host
# Then open: http://localhost:8100
```

See **[deployment/SETUP_GUIDE.md](deployment/SETUP_GUIDE.md)** for detailed instructions.

## Available Scopes

FirstShift Gateway organizes entities into 6 scopes:

- **ops** (27) - Operations and audit trails
- **data** (63) - Core business data
- **config** (51) - Configuration settings
- **metadata** (78) - Entity metadata
- **rbac** (8) - Role-based access control
- **globalmeta** (12) - Global metadata

**Total: 239+ entities**

## Development

```bash
# Run tests
uv run pytest

# Type checking
uv run mypy fsgw

# Format code
uv run ruff format fsgw
uv run ruff check fsgw --fix
```

## Documentation Website Features

The deployed documentation server provides:

- **Entity Browser** - Searchable table with 239+ entities
- **Entity Details** - Complete field metadata with primary keys
- **API Reference** - Authentication, endpoints, examples
- **Code Examples** - Python SDK, REST API (curl), CLI
- **JSON API** - Programmatic access at `/api/*`
- **Interactive Docs** - Swagger UI and ReDoc

## Requirements

- Python 3.11+
- httpx
- pydantic >= 2.8.0
- typer
- rich
- FastAPI (for documentation server)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FSGW_GATEWAY_URL` | FirstShift Gateway URL | Required |
| `FSGW_USERNAME` | Your username | Required |
| `FSGW_PASSWORD` | Your password | Required |
| `FSGW_TENANT_ID` | Tenant ID | `7` |

## Relationship to shiftfm

fsgw complements shiftfm (FirstShift FM SDK):

- **shiftfm**: Domain-specific SDK for forecasting, planning, workbench
- **fsgw**: Generic SDK for dynamic discovery and querying
- **Shared Auth**: Both use the same authentication mechanism

## License

Proprietary - FirstShift AI

## Support

For issues and questions:
- Check **[QUICKSTART.md](QUICKSTART.md)** for usage patterns
- See **[deployment/SETUP_GUIDE.md](deployment/SETUP_GUIDE.md)** for deployment help
- Review [docs/](docs/) for additional documentation

---

**Built with ❤️ by FirstShift AI** - Part of the FirstShift platform
