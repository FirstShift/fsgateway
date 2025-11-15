"""
API Discovery Example.

This script demonstrates how to discover all available entities
and their metadata programmatically.
"""

import asyncio
import os

from fsgw import FSGWClient


async def discover_api(client: FSGWClient):
    """
    Discover all entities and their metadata.

    Args:
        client: FSGWClient instance
    """
    print("Starting API discovery...\n")

    # Step 1: List all endpoints
    print("[1] Discovering entities...")
    endpoints = await client.list_endpoints()

    if not endpoints.success:
        print(f"Error: {endpoints.error}")
        return

    print(f"Found {endpoints.data.total_entities} entities across "
          f"{endpoints.data.total_groups} groups\n")

    # Step 2: Get metadata for each entity
    print("[2] Fetching metadata for each entity...\n")

    for group in endpoints.data.groups:
        print(f"Group: {group.name}")
        print("-" * 60)

        for entity in group.entities:
            print(f"\nEntity: {entity.name}")
            print(f"  Endpoint: {entity.endpoint}")
            print(f"  Methods: {', '.join(entity.methods)}")

            # Get metadata
            metadata = await client.get_metadata(entity=entity.name)

            if metadata.success:
                print(f"  Fields: {len(metadata.data.fields)}")

                if metadata.data.primary_keys:
                    print(f"  Primary Keys: {', '.join(metadata.data.primary_keys)}")

                # Show field summary
                field_types = {}
                for field in metadata.data.fields:
                    field_types[field.data_type] = field_types.get(field.data_type, 0) + 1

                print("  Field Types:")
                for dtype, count in sorted(field_types.items()):
                    print(f"    • {dtype}: {count}")
            else:
                print(f"  Error fetching metadata: {metadata.error}")

        print()

    print("\nDiscovery completed!")


async def main():
    """Main entry point."""
    # Get credentials from environment
    gateway_url = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
    tenant_id = int(os.getenv("FSGW_TENANT_ID", "7"))
    username = os.getenv("FSGW_USERNAME", "")
    password = os.getenv("FSGW_PASSWORD", "")

    if not username or not password:
        print("Error: FSGW_USERNAME and FSGW_PASSWORD must be set")
        return

    async with FSGWClient(
        gateway_url=gateway_url,
        tenant_id=tenant_id,
        username=username,
        password=password,
    ) as client:
        await discover_api(client)


if __name__ == "__main__":
    asyncio.run(main())
