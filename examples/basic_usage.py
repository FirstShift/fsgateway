"""
Basic usage examples for FSGW SDK.

This script demonstrates the three main API operations:
1. List all available endpoints
2. Get metadata for an entity
3. Query data from an entity
"""

import asyncio
import os

from fsgw import FSGWClient


async def main():
    """Run basic usage examples."""
    # Get credentials from environment
    gateway_url = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
    tenant_id = int(os.getenv("FSGW_TENANT_ID", "7"))
    username = os.getenv("FSGW_USERNAME", "")
    password = os.getenv("FSGW_PASSWORD", "")

    if not username or not password:
        print("Error: FSGW_USERNAME and FSGW_PASSWORD must be set")
        return

    # Create client
    async with FSGWClient(
        gateway_url=gateway_url,
        tenant_id=tenant_id,
        username=username,
        password=password,
    ) as client:
        print("=" * 80)
        print("FirstShift API Gateway - Basic Usage Examples")
        print("=" * 80)

        # Example 1: List all available endpoints
        print("\n[1] Listing all available endpoints...")
        print("-" * 80)

        endpoints = await client.list_endpoints()
        if endpoints.success:
            print(f"✓ Found {endpoints.data.total_groups} groups with "
                  f"{endpoints.data.total_entities} entities\n")

            for group in endpoints.data.groups:
                print(f"Group: {group.name}")
                for entity in group.entities:
                    print(f"  • {entity.name}: {entity.endpoint}")
                print()
        else:
            print(f"✗ Error: {endpoints.error}")

        # Example 2: Get metadata for an entity
        # Note: Replace 'products' with an actual entity name from your API
        print("\n[2] Getting metadata for 'products' entity...")
        print("-" * 80)

        metadata = await client.get_metadata(entity="products")
        if metadata.success:
            print(f"✓ Entity: {metadata.data.entity}")
            print(f"  Fields: {len(metadata.data.fields)}")
            print(f"  Primary Keys: {', '.join(metadata.data.primary_keys)}\n")

            print("Fields:")
            for field in metadata.data.fields[:5]:  # Show first 5 fields
                pk_marker = " [PK]" if field.is_primary_key else ""
                req_marker = " [Required]" if field.required else ""
                print(f"  • {field.name}: {field.data_type}{pk_marker}{req_marker}")

            if len(metadata.data.fields) > 5:
                print(f"  ... and {len(metadata.data.fields) - 5} more fields")
        else:
            print(f"✗ Error: {metadata.error}")

        # Example 3: Query data from an entity
        print("\n[3] Querying data from 'products' entity...")
        print("-" * 80)

        results = await client.query(
            entity="products",
            filters={"status": "active"},
            sort_by="name",
            limit=5,
        )

        if results.success:
            print(f"✓ Found {results.data.total} total records")
            print(f"  Showing page {results.data.page} of {results.data.total_pages}\n")

            print("Results:")
            for i, item in enumerate(results.data.items, 1):
                print(f"  {i}. {item}")
        else:
            print(f"✗ Error: {results.error}")

        print("\n" + "=" * 80)
        print("Examples completed!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
