# FSGW Setup Guide

Quick setup guide for the FirstShift API Gateway SDK.

## Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- FirstShift API credentials

## Installation

### 1. Install Dependencies

Using uv (recommended):
```bash
cd /Users/al/Projects/firstshift/fsgateway
uv sync
```

Using pip:
```bash
pip install -e .
```

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```bash
FSGW_GATEWAY_URL=https://dev-cloudgateway.firstshift.ai
FSGW_TENANT_ID=7
FSGW_USERNAME=your-username
FSGW_PASSWORD=your-password
```

Load environment variables:
```bash
source .env  # or export $(cat .env | xargs)
```

## Quick Start

### Using Python SDK

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
        # List endpoints
        endpoints = await client.list_endpoints()
        print(endpoints.data)

        # Get metadata
        metadata = await client.get_metadata(entity="products")
        print(metadata.data)

        # Query data
        results = await client.query(
            entity="products",
            filters={"status": "active"},
            limit=10
        )
        print(results.data)

asyncio.run(main())
```

### Using CLI

```bash
# List all endpoints
fsgw endpoints

# Get metadata for an entity
fsgw metadata products

# Query data
fsgw query products --filter "status=active" --limit 10

# Get help
fsgw --help
```

### Using Web Server

Start the FastAPI server:
```bash
fsgw-server
# or
make server
```

Then visit:
- http://localhost:8000 - API info
- http://localhost:8000/docs - Interactive documentation (Swagger UI)
- http://localhost:8000/redoc - Alternative documentation (ReDoc)

## Running Examples

### Basic Usage Example

```bash
python examples/basic_usage.py
```

This demonstrates:
- Listing all available endpoints
- Getting metadata for an entity
- Querying data with filters

### API Discovery Example

```bash
python examples/discovery.py
```

This script:
- Discovers all entities in the API
- Fetches metadata for each entity
- Displays field information and types

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
uv run pytest tests/test_client.py -v
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Run all checks
make check
```

### Project Structure

```
fsgw/
├── __init__.py           # Package entry point
├── auth/                 # Authentication module
├── client/               # Main client and HTTP layer
├── models/               # Data models
├── cli/                  # CLI tool
└── server/               # FastAPI server

examples/                 # Usage examples
tests/                    # Test suite
docs/                     # Documentation
```

## Troubleshooting

### Authentication Errors

If you see authentication errors:
1. Verify your credentials are correct in `.env`
2. Ensure `FSGW_USERNAME` and `FSGW_PASSWORD` are exported
3. Check that the gateway URL is correct

### Import Errors

If you get import errors:
1. Ensure you've installed the package: `uv sync` or `pip install -e .`
2. Check that you're in the correct virtual environment

### Connection Errors

If you can't connect to the API:
1. Verify the gateway URL is correct
2. Check your network connection
3. Ensure the API is accessible from your location

## Next Steps

1. **Read the Documentation**: See [README.md](README.md) for detailed documentation
2. **Explore the API**: Use the CLI or web server to explore available entities
3. **Build SDK Methods**: Extend the client with domain-specific methods
4. **Create TypeScript SDK**: Use the same pattern to build a TypeScript/JavaScript SDK

## Related Projects

- **shiftfm**: FirstShift FM SDK for forecasting and planning
- **vibeSCM**: FirstShift workspace platform

## Support

For issues or questions:
- Check the [README.md](README.md) for detailed documentation
- Review the [examples/](examples/) directory for usage patterns
- Create a GitHub issue with reproduction steps
