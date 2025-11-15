# FirstShift Gateway SDK Documentation

This directory contains internal documentation for the FSGW SDK project.

## Documentation Index

### For Users
- **[../QUICKSTART.md](../QUICKSTART.md)** - Quick start guide with examples
- **[../README.md](../README.md)** - Main project overview and features

### For Developers

#### Project Status
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)** - Current project state and what's working
- **[phases/SDK_DEVELOPMENT_CHECKLIST.md](phases/SDK_DEVELOPMENT_CHECKLIST.md)** - Development roadmap and progress

#### Phase Documentation
- **[phases/PHASE1_COMPLETE.md](phases/PHASE1_COMPLETE.md)** - Phase 1: Core Models completion report
- **[phases/PHASE2_COMPLETE.md](phases/PHASE2_COMPLETE.md)** - Phase 2: Client Infrastructure completion report

#### API Documentation
- **[API_DISCOVERY_SUMMARY.md](API_DISCOVERY_SUMMARY.md)** - Complete list of 239+ discovered entities
- **[api/FirstShift_Metadata_Query_API_Doc.xml](api/FirstShift_Metadata_Query_API_Doc.xml)** - Original API specification

### For Deployment
- **[../deployment/SETUP_GUIDE.md](../deployment/SETUP_GUIDE.md)** - Step-by-step deployment guide
- **[../deployment/ARCHITECTURE.md](../deployment/ARCHITECTURE.md)** - System architecture diagrams
- **[../deployment/DEPLOYMENT.md](../deployment/DEPLOYMENT.md)** - Advanced deployment options

## Quick Links

### Running the SDK

**Python SDK:**
```python
from fsgw.client import FSGWClient

async with FSGWClient(...) as client:
    entities = await client.list_apis()
    metadata = await client.get_metadata("ops/auditTrail")
    results = await client.query("ops/auditTrail")
```

**CLI:**
```bash
uv run fsgw interactive    # Interactive REPL
uv run fsgw entities       # List all entities
uv run fsgw info ops/auditTrail  # Get details
```

**Documentation Server:**
```bash
uv run fsgw server  # http://localhost:8000
```

## Documentation Organization

```
docs/
├── README.md                      # This file
├── CURRENT_STATUS.md              # Current project status
├── API_DISCOVERY_SUMMARY.md       # Entity discovery results
├── phases/                        # Development phases
│   ├── SDK_DEVELOPMENT_CHECKLIST.md
│   ├── PHASE1_COMPLETE.md
│   └── PHASE2_COMPLETE.md
└── api/                           # API specifications
    └── FirstShift_Metadata_Query_API_Doc.xml
```

## What's Complete ✅

- ✅ **Phase 1**: Core Models (Pydantic models with type safety)
- ✅ **Phase 2**: Client Infrastructure (HTTP client, auth, error handling)
- ✅ **Phase 3**: API Methods (Discovery, Metadata, Query)
- ✅ **Phase 6**: Error Handling (11 custom exceptions)
- ✅ **Phase 3.5**: CLI & Documentation Website (bonus)

## What's Next

See [CURRENT_STATUS.md](CURRENT_STATUS.md) for:
- Detailed completion status
- Usage examples
- Next steps and priorities
- Optional enhancements

## Key Statistics

- **Total Lines**: ~3,500+ lines of code
- **Entities Available**: 239+ across 6 scopes
- **Scopes**: ops, data, config, metadata, rbac, globalmeta
- **Test Coverage**: Integration tests complete, unit tests pending

## Contributing to Documentation

When updating documentation:

1. **Status Updates**: Update [CURRENT_STATUS.md](CURRENT_STATUS.md)
2. **Phase Progress**: Update [phases/SDK_DEVELOPMENT_CHECKLIST.md](phases/SDK_DEVELOPMENT_CHECKLIST.md)
3. **User Guides**: Update [../QUICKSTART.md](../QUICKSTART.md) or [../README.md](../README.md)
4. **This Index**: Update this README.md to reflect new documentation

## Support

For questions about the project:
- Check [CURRENT_STATUS.md](CURRENT_STATUS.md) for current state
- Review [phases/SDK_DEVELOPMENT_CHECKLIST.md](phases/SDK_DEVELOPMENT_CHECKLIST.md) for roadmap
- See [../QUICKSTART.md](../QUICKSTART.md) for usage examples
- Try the interactive docs: `uv run fsgw server`

---

**Last Updated**: 2025-11-15
