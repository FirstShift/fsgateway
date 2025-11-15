# FirstShift Gateway SDK Documentation

This directory contains all documentation for the FSGW SDK project.

## Directory Structure

```
docs/
├── phases/          # Development phase documentation
│   ├── PHASE1_COMPLETE.md
│   ├── PHASE2_COMPLETE.md
│   └── SDK_DEVELOPMENT_CHECKLIST.md
├── guides/          # User and developer guides
│   ├── GETTING_STARTED.md
│   ├── SETUP.md
│   ├── PROJECT_SUMMARY.md
│   └── CHECKLIST.md
├── api/             # API documentation
│   ├── API_DISCOVERY_SUMMARY.md
│   └── FirstShift_Metadata_Query_API_Doc.xml
└── README.md        # This file
```

## Documentation Formats

### 1. Interactive Web Documentation

The SDK includes a comprehensive FastAPI-based documentation server that auto-discovers all 239+ entities:

**Start the server:**
```bash
fsgw-server

# Or with custom settings
fsgw server --host 0.0.0.0 --port 8000 --reload
```

**Access the documentation:**
- Landing page: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Features:**
- Browse all entities by scope
- View detailed field metadata
- Interactive query examples with curl commands
- Search entities by name or description
- Live API health monitoring

### 2. CLI Documentation

Query documentation directly from the command line:

```bash
# List all entities
fsgw entities

# Filter by scope
fsgw entities --scope ops

# Get entity details
fsgw info ops/auditTrail

# Search entities
fsgw search audit

# Ask questions in natural language
fsgw ask "What entities are in the ops scope?"
fsgw ask "Show me audit trail fields"
fsgw ask "How do I query data?"
```

### 3. Static Documentation

-  **[Phase Documentation](phases/)**: Development progress and completion reports
- **[User Guides](guides/)**: Getting started and setup instructions
- **[API Discovery](api/)**: Complete list of discovered entities

## Quick Start

1. **Set up credentials:**
   ```bash
   export FSGW_USERNAME="your-username"
   export FSGW_PASSWORD="your-password"
   export FSGW_TENANT_ID="7"
   export FSGW_GATEWAY_URL="https://dev-cloudgateway.firstshift.ai"
   ```

2. **Start documentation server:**
   ```bash
   fsgw-server
   ```

3. **Browse entities:**
   - Visit http://localhost:8000
   - Or use CLI: `fsgw entities`

4. **Get entity metadata:**
   ```bash
   fsgw info ops/auditTrail
   ```

5. **Query data:**
   ```bash
   fsgw query ops/auditTrail --limit 10
   ```

## API Endpoints

The documentation server provides the following REST API endpoints:

### Discovery
- `GET /entities` - List all entities grouped by scope
- `GET /entities/{scope}` - Filter entities by scope
- `GET /search?q={term}` - Search entities

### Metadata
- `GET /entities/{scope}/{entity}/metadata` - Get field information
- `GET /entities/{scope}/{entity}/query` - Get query examples

### Health
- `GET /health` - Server and API health check

## Entity Organization

Entities are organized into 6 scopes:

1. **config** - Configuration entities
2. **data** - Data entities
3. **globalmeta** - Global metadata
4. **metadata** - Metadata entities
5. **ops** - Operations entities (audit trail, etc.)
6. **rbac** - Role-based access control

## Usage Examples

### Python SDK
```python
from fsgw import FSGWClient, QueryRequest

async with FSGWClient(
    gateway_url="https://dev-cloudgateway.firstshift.ai",
    username="user",
    password="pass",
    tenant_id=7,
) as client:
    # List entities
    entities = await client.list_apis()

    # Get metadata
    metadata = await client.get_metadata("ops/auditTrail")

    # Query data
    query = QueryRequest().add_filter("tenantId", "=", 7).limit(10)
    results = await client.query("ops/auditTrail", query)
```

### CLI
```bash
# List all entities
fsgw entities

# Get entity info
fsgw info ops/auditTrail

# Query data
fsgw query ops/auditTrail --filter tenantId=7 --limit 10

# Search
fsgw search audit

# Ask questions
fsgw ask "What entities are in ops scope?"
```

### REST API
```bash
# List all entities
curl http://localhost:8000/entities

# Get metadata
curl http://localhost:8000/entities/ops/auditTrail/metadata

# Search
curl "http://localhost:8000/search?q=audit"
```

## Development Documentation

- [SDK Development Checklist](phases/SDK_DEVELOPMENT_CHECKLIST.md) - Complete roadmap
- [Phase 1: Core Models](phases/PHASE1_COMPLETE.md) - Pydantic models and validation
- [Phase 2: Client Infrastructure](phases/PHASE2_COMPLETE.md) - HTTP client and authentication

## Contributing

When adding new documentation:

1. Place phase documentation in `phases/`
2. Place user guides in `guides/`
3. Place API documentation in `api/`
4. Update this README with new sections

## Support

For issues or questions:
- GitHub Issues: https://github.com/FirstShift/fsgateway/issues
- Documentation Server: http://localhost:8000
- CLI Help: `fsgw --help`
