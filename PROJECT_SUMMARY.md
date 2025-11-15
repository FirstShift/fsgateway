# FSGW Project Summary

## Overview

**fsgw** is a Python SDK for the FirstShift API Gateway that provides dynamic discovery, metadata introspection, and generic querying capabilities for any entity exposed by the FirstShift platform.

## Project Status

✅ **Project Structure Complete** - Ready for API implementation

### What's Done

- ✅ Complete package structure with `pyproject.toml`
- ✅ Authentication module (adapted from shiftfm)
- ✅ Core client with async HTTP support
- ✅ Data models for all three APIs
- ✅ CLI tool with Typer
- ✅ FastAPI server for web-based exploration
- ✅ Test suite structure
- ✅ Examples and documentation
- ✅ Development tooling (Makefile, linting, formatting)

### What's Next

The project structure is complete, but the actual API endpoints need to be implemented based on the real API specification in `docs/FirstShift_Metadata_Query_API_Doc.docx`.

**Next Steps:**

1. **Extract API Specification** - Read the .docx file to understand actual endpoints
2. **Update Client Methods** - Modify the three API methods to match real endpoints
3. **Test with Real API** - Test authentication and endpoints against dev environment
4. **Iterate and Refine** - Adjust models and methods based on actual responses
5. **Build TypeScript SDK** - Create parallel implementation for JavaScript/TypeScript

## Project Architecture

### Three Core APIs

1. **API #1 - List All Available Endpoints**
   - Discovers all API groups and entities
   - Returns endpoint paths and supported methods
   - Implemented in: `fsgw/client/client.py::list_endpoints()`

2. **API #2 - Get Metadata for Any Entity**
   - Returns field-level schema information
   - Includes data types, constraints, primary keys
   - Implemented in: `fsgw/client/client.py::get_metadata()`

3. **API #3 - Query Data for Any Entity**
   - Generic querying with filters, sorting, pagination
   - Supports field projections
   - Implemented in: `fsgw/client/client.py::query()`

### Key Components

#### Client Layer ([fsgw/client/](fsgw/client/))
- `client.py` - Main `FSGWClient` class with three API methods
- `models.py` - HTTP response types, error handling
- Async-first design with `httpx`
- Automatic authentication management

#### Data Models ([fsgw/models/](fsgw/models/))
- `endpoints.py` - Models for API #1 (discovery)
- `metadata.py` - Models for API #2 (schema)
- `query.py` - Models for API #3 (querying)
- All models use Pydantic v2 for validation

#### Authentication ([fsgw/auth/](fsgw/auth/))
- Adapted from shiftfm SDK
- JWT token management
- Automatic token refresh support
- Compatible with existing FirstShift auth

#### CLI Tool ([fsgw/cli/](fsgw/cli/))
- Built with Typer
- Commands: `endpoints`, `metadata`, `query`
- Rich terminal output
- Environment-based configuration

#### FastAPI Server ([fsgw/server/](fsgw/server/))
- Web-based API explorer
- Interactive documentation (Swagger UI)
- REST endpoints mirroring SDK methods
- Health checks and monitoring

## Directory Structure

```
fsgateway/
├── fsgw/                          # Main package
│   ├── __init__.py               # Package entry point
│   ├── auth/                     # Authentication
│   │   ├── __init__.py
│   │   └── models.py
│   ├── client/                   # Core client
│   │   ├── __init__.py
│   │   ├── client.py            # FSGWClient (main class)
│   │   └── models.py            # HTTP models
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   ├── endpoints.py         # API #1 models
│   │   ├── metadata.py          # API #2 models
│   │   └── query.py             # API #3 models
│   ├── cli/                      # CLI tool
│   │   ├── __init__.py
│   │   └── main.py              # CLI entry point
│   └── server/                   # FastAPI server
│       ├── __init__.py
│       └── main.py              # Server entry point
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_client.py
│   └── test_models.py
│
├── examples/                     # Usage examples
│   ├── basic_usage.py
│   └── discovery.py
│
├── docs/                         # Documentation
│   └── FirstShift_Metadata_Query_API_Doc.docx
│
├── pyproject.toml               # Package configuration
├── README.md                    # Main documentation
├── SETUP.md                     # Setup guide
├── PROJECT_SUMMARY.md           # This file
├── Makefile                     # Development commands
├── .env.example                 # Environment template
└── .gitignore                   # Git ignore rules
```

## Design Principles

### 1. Pattern Consistency with shiftfm
- Same authentication mechanism
- Same async/await patterns
- Same Pydantic models approach
- Compatible client initialization

### 2. Generic and Extensible
- Works with any entity dynamically
- No hard-coded entity types
- Easy to extend with custom methods
- Type-safe throughout

### 3. Developer-Friendly
- Clear, explicit API
- Comprehensive documentation
- Interactive tools (CLI, web server)
- Examples and guides

### 4. Production-Ready Structure
- Proper error handling
- Logging and observability (Logfire)
- Test suite ready
- Code quality tooling

## Usage Patterns

### Pattern 1: SDK Library

```python
from fsgw import FSGWClient

async with FSGWClient(...) as client:
    endpoints = await client.list_endpoints()
    metadata = await client.get_metadata("products")
    results = await client.query("products", filters={"status": "active"})
```

### Pattern 2: CLI Tool

```bash
fsgw endpoints
fsgw metadata products
fsgw query products --filter "status=active"
```

### Pattern 3: Web API

```bash
fsgw-server
curl http://localhost:8000/endpoints
curl http://localhost:8000/metadata/products
curl -X POST http://localhost:8000/query/products -d '{"filters": {"status": "active"}}'
```

## Integration with Existing Projects

### With shiftfm

```python
from shiftfm import ShiftFMClient
from fsgw import FSGWClient

# Both use same auth
async with ShiftFMClient(...) as fm_client:
    forecasts = await fm_client.forecasting.get_forecast_run_history()

async with FSGWClient(...) as gw_client:
    entities = await gw_client.list_endpoints()
```

### Future: TypeScript SDK

The same pattern can be replicated for TypeScript:

```typescript
import { FSGWClient } from '@firstshift/fsgw';

const client = new FSGWClient({
  gatewayUrl: 'https://dev-cloudgateway.firstshift.ai',
  tenantId: 7,
  username: 'user',
  password: 'pass'
});

const endpoints = await client.listEndpoints();
const metadata = await client.getMetadata('products');
const results = await client.query('products', { filters: { status: 'active' } });
```

## Development Workflow

### 1. Setup
```bash
uv sync                  # Install dependencies
cp .env.example .env     # Configure environment
```

### 2. Development
```bash
make format             # Format code
make lint               # Check code quality
make test               # Run tests
```

### 3. Testing
```bash
python examples/basic_usage.py      # Test SDK
fsgw endpoints                      # Test CLI
fsgw-server                         # Test server
```

### 4. Documentation
- Update README.md for new features
- Add examples for common use cases
- Document any API changes

## Configuration

### Environment Variables

```bash
FSGW_GATEWAY_URL         # API gateway URL
FSGW_TENANT_ID           # Tenant identifier
FSGW_USERNAME            # Authentication username
FSGW_PASSWORD            # Authentication password
LOGFIRE_IGNORE_NO_CONFIG # Suppress Logfire warnings
```

### Client Configuration

```python
FSGWClient(
    gateway_url="...",
    tenant_id=7,
    username="...",
    password="...",
    timeout=30,              # Request timeout
    auto_refresh=True,       # Auto-refresh tokens
    refresh_lead_time=300,   # Refresh 5 min before expiry
)
```

## Key Files

### Entry Points
- `fsgw/__init__.py` - Package exports
- `fsgw/cli/main.py` - CLI entry point (`fsgw` command)
- `fsgw/server/main.py` - Server entry point (`fsgw-server` command)

### Core Implementation
- `fsgw/client/client.py` - Main client with three API methods
- `fsgw/client/models.py` - HTTP response handling
- `fsgw/auth/models.py` - Authentication models

### Data Models
- `fsgw/models/endpoints.py` - Discovery models
- `fsgw/models/metadata.py` - Schema models
- `fsgw/models/query.py` - Query models

## Testing Strategy

### Unit Tests
- Model validation
- Client initialization
- URL normalization
- Error handling

### Integration Tests (TODO)
- Real API authentication
- Endpoint discovery
- Metadata fetching
- Data querying

### E2E Tests (TODO)
- Complete workflows
- Error scenarios
- Performance testing

## Future Enhancements

### Short Term
1. Implement actual API endpoints based on documentation
2. Add comprehensive error messages
3. Add retry logic with exponential backoff
4. Implement token refresh
5. Add request/response logging

### Medium Term
1. Generate TypeScript SDK
2. Add caching layer for metadata
3. Build SDK generator tool
4. Create Postman collection
5. Add performance monitoring

### Long Term
1. GraphQL support
2. WebSocket support for real-time data
3. Batch operations
4. Advanced filtering DSL
5. Plugin system for custom entity types

## Relationship to Other Projects

```
┌─────────────────────────────────────────────────────┐
│                 FirstShift Platform                  │
└─────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
┌─────────▼─────────┐         ┌──────────▼──────────┐
│    FM APIs        │         │   API Gateway       │
│  (Forecasting)    │         │   (Generic)         │
└─────────┬─────────┘         └──────────┬──────────┘
          │                               │
          │                               │
┌─────────▼─────────┐         ┌──────────▼──────────┐
│   shiftfm SDK     │         │    fsgw SDK         │
│   (Python)        │         │    (Python)         │
│                   │◄────────┤                     │
│ • Forecasting     │  Shared │ • Discovery         │
│ • Planning        │   Auth  │ • Metadata          │
│ • Workbench       │         │ • Query             │
└───────────────────┘         └─────────────────────┘
```

## Success Criteria

✅ **Structure Complete**
- Package structure established
- All modules created
- Tests framework ready
- Documentation written

⏳ **Implementation Pending**
- API endpoints need real specification
- Authentication needs testing
- Models may need adjustment
- CLI/Server need real data

🎯 **Future Goals**
- TypeScript SDK
- Complete test coverage
- Production deployment
- Multi-language support

## Contact & Support

For questions or issues:
- Review documentation in README.md and SETUP.md
- Check examples in examples/
- Refer to shiftfm SDK for patterns
- Create GitHub issue for bugs

---

**Status**: Project structure complete, ready for API implementation
**Last Updated**: 2025-11-15
**Version**: 0.1.0
