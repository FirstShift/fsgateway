# Discovery Artifacts

This directory contains all artifacts from the API discovery process.

## Directory Structure

```
.discovery/
├── raw/                    # Raw test outputs during discovery
│   ├── auth_response.json          # Authentication test response
│   ├── api1_response.json          # API #1 initial test
│   ├── metadata_*.json             # Metadata test responses
│   └── query_*.json                # Query test responses
│
├── results/                # Complete discovery results
│   ├── complete_discovery.json     # Full discovery with all 239 entities
│   ├── all_entities.json           # List of all entities from API #1
│   └── entity_*.json               # Individual entity files (239 files)
│
├── scripts/                # Discovery scripts (archived)
│   ├── complete_api_discovery.py   # Main discovery script
│   ├── comprehensive_discovery.py  # Initial discovery script
│   └── test_*.py                   # Various test scripts
│
└── logs/                   # Discovery logs
    └── discovery_output.log        # Complete discovery run log
```

## Key Files

### `results/complete_discovery.json` (1.9 MB)
Complete documentation of all 239 entities including:
- Entity metadata (field names, types, constraints)
- Sample data (up to 5 records per entity)
- Statistics and summaries

### `results/all_entities.json`
List of all 239 entities from API #1 with:
- apiScope
- apiUrl
- externalAPIName
- description

### `results/entity_*.json` (239 files)
Individual entity documentation files, one per entity.

## Discovery Summary

- **Total entities**: 239
- **Entities with metadata**: 239 (100%)
- **Entities with data**: 126 (53%)

### By Scope
- config: 51 entities (31 with data)
- data: 63 entities (15 with data)
- globalmeta: 12 entities (11 with data)
- metadata: 78 entities (53 with data)
- ops: 27 entities (10 with data)
- rbac: 8 entities (6 with data)

## Running Discovery Again

To re-run the complete discovery:

```bash
# Set credentials
export FSGW_USERNAME="your-email@example.com"
export FSGW_PASSWORD="your-password"
export FSGW_TENANT_ID="7"

# Run discovery (from project root)
python3 .discovery/scripts/complete_api_discovery.py
```

## Documentation

See [docs/API_DISCOVERY_SUMMARY.md](../docs/API_DISCOVERY_SUMMARY.md) for complete API documentation.
