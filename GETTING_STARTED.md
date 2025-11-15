# Getting Started with FSGW

Welcome! This guide will get you up and running with the FirstShift API Gateway SDK in minutes.

## What is FSGW?

FSGW (FirstShift Gateway) is a Python SDK that provides:
- 🔍 **Dynamic Discovery** - Find all available API entities
- 📊 **Metadata Introspection** - Get schema information for any entity
- 🔎 **Generic Querying** - Query any entity with filters and pagination

## Quick Install

```bash
cd /Users/al/Projects/firstshift/fsgateway
uv sync
```

## Set Up Credentials

```bash
cp .env.example .env
# Edit .env with your credentials
export $(cat .env | xargs)
```

## Your First Request

### Option 1: Python SDK

Create a file `test.py`:

```python
import asyncio
from fsgw import FSGWClient

async def main():
    async with FSGWClient(
        gateway_url="https://dev-cloudgateway.firstshift.ai",
        tenant_id=7,
        username="your-username",
        password="your-password"
    ) as client:
        # Discover all available entities
        endpoints = await client.list_endpoints()

        if endpoints.success:
            print(f"Found {endpoints.data.total_entities} entities!")
            for group in endpoints.data.groups:
                print(f"\nGroup: {group.name}")
                for entity in group.entities:
                    print(f"  - {entity.name}")
        else:
            print(f"Error: {endpoints.error}")

asyncio.run(main())
```

Run it:
```bash
python test.py
```

### Option 2: CLI

```bash
# List all available entities
fsgw endpoints

# Get schema for an entity (replace 'products' with actual entity)
fsgw metadata products

# Query data
fsgw query products --limit 5
```

### Option 3: Web Interface

```bash
# Start the web server
fsgw-server

# Open browser to http://localhost:8000/docs
```

## What Can You Do?

### 1. Discover APIs

Find out what entities are available:

```python
endpoints = await client.list_endpoints()

for group in endpoints.data.groups:
    print(f"Group: {group.name}")
    for entity in group.entities:
        print(f"  {entity.name}: {entity.endpoint}")
```

### 2. Get Schema Information

Learn about entity fields and types:

```python
metadata = await client.get_metadata(entity="products")

for field in metadata.data.fields:
    print(f"{field.name}: {field.data_type}")
    if field.is_primary_key:
        print("  ^ This is a primary key")
```

### 3. Query Data

Fetch data with filters and sorting:

```python
results = await client.query(
    entity="products",
    filters={"category": "electronics"},
    sort_by="price",
    sort_order="desc",
    limit=10
)

for item in results.data.items:
    print(item)
```

## Common Tasks

### Task 1: Find All Customer Data

```python
# 1. Check if 'customers' entity exists
endpoints = await client.list_endpoints()

# 2. Get customer schema
metadata = await client.get_metadata("customers")
print(f"Customer fields: {[f.name for f in metadata.data.fields]}")

# 3. Query customer data
results = await client.query("customers", limit=100)
```

### Task 2: Filter and Sort Results

```python
results = await client.query(
    entity="orders",
    filters={
        "status": "completed",
        "total": {"$gt": 1000}  # Orders over $1000
    },
    sort_by="created_at",
    sort_order="desc",
    limit=20
)
```

### Task 3: Paginate Through Results

```python
page = 1
while True:
    results = await client.query(
        entity="products",
        page=page,
        limit=50
    )

    # Process items
    for item in results.data.items:
        print(item)

    # Check if more pages
    if not results.data.has_next:
        break

    page += 1
```

## CLI Quick Reference

```bash
# Discovery
fsgw endpoints                      # List all entities
fsgw metadata <entity>              # Get entity schema

# Querying
fsgw query <entity>                 # Get all records
fsgw query <entity> --limit 10      # Limit results
fsgw query <entity> --filter "key=value"  # Filter
fsgw query <entity> --sort-by name  # Sort results
fsgw query <entity> --output json   # JSON output
fsgw query <entity> --output csv    # CSV output

# Server
fsgw-server                         # Start on :8000
fsgw-server --port 3000             # Custom port
fsgw-server --reload                # Auto-reload (dev)
```

## Examples

Run the included examples:

```bash
# Basic usage demonstration
python examples/basic_usage.py

# Complete API discovery
python examples/discovery.py
```

## Development

### Run Tests

```bash
make test
```

### Format Code

```bash
make format
```

### Check Code Quality

```bash
make check
```

## Next Steps

1. **Explore the API** - Use `fsgw endpoints` to see what's available
2. **Read the Docs** - Check [README.md](README.md) for detailed docs
3. **View Examples** - Look at `examples/` for more patterns
4. **Build Features** - Extend the SDK for your use case

## Need Help?

- 📖 **Documentation**: [README.md](README.md)
- 🚀 **Setup Guide**: [SETUP.md](SETUP.md)
- 📋 **Project Info**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- 💡 **Examples**: `examples/` directory

## Common Issues

### "FSGW_USERNAME and FSGW_PASSWORD must be set"

Make sure you've exported your environment variables:
```bash
export $(cat .env | xargs)
```

### "Module not found: fsgw"

Install the package:
```bash
uv sync
# or
pip install -e .
```

### "Connection refused"

Check that:
1. The gateway URL is correct
2. You have network access
3. The API is running

## Project Structure

```
fsgateway/
├── fsgw/              # Main SDK package
│   ├── client/        # HTTP client
│   ├── models/        # Data models
│   ├── cli/           # CLI tool
│   └── server/        # Web server
├── examples/          # Usage examples
├── tests/             # Test suite
└── docs/              # Documentation
```

---

**Ready to explore?** Run `fsgw endpoints` to see what's available!
