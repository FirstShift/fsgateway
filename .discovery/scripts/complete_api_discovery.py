#!/usr/bin/env python3
"""
Complete API Discovery Script - All Three APIs Working

This script systematically:
1. Lists all available API endpoints (API #1)
2. Gets metadata for each endpoint (API #2)
3. Queries sample data from each endpoint (API #3)

Saves comprehensive documentation of the entire API structure.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx


# Configuration
GATEWAY_URL = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
USERNAME = os.getenv("FSGW_USERNAME", "")
PASSWORD = os.getenv("FSGW_PASSWORD", "")
TENANT_ID = int(os.getenv("FSGW_TENANT_ID", "7"))


async def authenticate() -> str:
    """Authenticate and return access token."""
    # Check if we have a cached token from auth_response.json
    auth_cache = Path(__file__).parent.parent / "auth_response.json"
    if auth_cache.exists():
        try:
            with open(auth_cache) as f:
                cached = json.load(f)
                token = cached["data"]["access-token"]
                print("✓ Using cached authentication token\n")
                return token
        except Exception:
            pass

    # Otherwise authenticate with credentials
    if not USERNAME or not PASSWORD:
        raise ValueError(
            "Please set FSGW_USERNAME and FSGW_PASSWORD environment variables"
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GATEWAY_URL}/auth/login",
            json={"userName": USERNAME, "password": PASSWORD, "tenantId": TENANT_ID},
            timeout=30.0,
        )
        response.raise_for_status()
        token = response.json()["data"]["access-token"]
        print("✓ Authenticated\n")
        return token


async def get_all_apis(token: str) -> list[dict[str, Any]]:
    """API #1 - Get list of all available endpoints."""
    print("=" * 80)
    print("API #1: Discovering all endpoints...")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GATEWAY_URL}/api/v1/meta/apis",
            headers={"access-token": token},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        entities = data.get("data", [])

        # Group by scope
        by_scope = {}
        for entity in entities:
            scope = entity.get("apiScope", "unknown")
            if scope not in by_scope:
                by_scope[scope] = []
            by_scope[scope].append(entity)

        print(f"\nTotal entities: {len(entities)}")
        print("\nBreakdown by scope:")
        for scope, items in sorted(by_scope.items()):
            print(f"  {scope:15s}: {len(items):3d} entities")

        return entities


async def get_metadata(token: str, api_url: str) -> dict[str, Any] | None:
    """API #2 - Get metadata for a specific entity."""
    scope, entity = api_url.split("/", 1)
    endpoint = f"{GATEWAY_URL}/api/v1/meta/{scope}/{entity}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                endpoint,
                headers={"access-token": token},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ⚠️  Failed to get metadata: {e}")
            return None


async def query_data(
    token: str, api_url: str, limit: int = 3
) -> dict[str, Any] | None:
    """API #3 - Query data from an entity."""
    scope, entity = api_url.split("/", 1)
    endpoint = f"{GATEWAY_URL}/api/v1/{scope}/{entity}/query"

    # Correct request body format from documentation
    payload = {
        "criteriaList": [],  # Empty = no filters
        "orderByList": [],  # No sorting
        "selectFieldsList": [],  # Empty = all fields
        "offset": 0,
        "limit": limit,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                endpoint,
                headers={"access-token": token, "Content-Type": "application/json"},
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Check internal status
            if data.get("status") == "SUCCESS":
                return data
            else:
                print(f"  ⚠️  Query returned status: {data.get('status')}")
                return None
        except Exception as e:
            print(f"  ⚠️  Failed to query data: {e}")
            return None


async def discover_all_entities(token: str, output_dir: Path):
    """Discover all entities with metadata and sample data."""
    # Step 1: Get all API endpoints
    entities = await get_all_apis(token)

    # Save the list
    with open(output_dir / "all_entities.json", "w") as f:
        json.dump(entities, f, indent=2)
    print(f"\n✓ Saved entity list to all_entities.json")

    # Step 2: For each entity, get metadata and sample data
    print("\n" + "=" * 80)
    print("API #2 & #3: Discovering metadata and sample data...")
    print("=" * 80)

    results = []
    for i, entity in enumerate(entities, 1):
        api_url = entity["apiUrl"]
        name = entity["externalAPIName"]
        scope = entity["apiScope"]

        print(f"\n[{i}/{len(entities)}] {api_url}")

        # Get metadata
        metadata = await get_metadata(token, api_url)
        if metadata:
            field_count = len(metadata.get("data", []))
            print(f"  ✓ Metadata: {field_count} fields")
        else:
            print(f"  ✗ Metadata: Failed")

        # Query sample data
        query_result = await query_data(token, api_url, limit=5)
        if query_result and query_result.get("data"):
            record_count = len(query_result["data"])
            print(f"  ✓ Query: {record_count} records")
        else:
            record_count = 0
            print(f"  ✓ Query: 0 records (empty table)")

        # Compile result
        result = {
            "apiUrl": api_url,
            "apiScope": scope,
            "externalAPIName": name,
            "description": entity.get("description", ""),
            "metadata": metadata,
            "sampleData": query_result,
            "fieldCount": len(metadata.get("data", [])) if metadata else 0,
            "recordCount": record_count,
        }
        results.append(result)

        # Save individual entity files
        safe_name = api_url.replace("/", "_")
        entity_file = output_dir / f"entity_{safe_name}.json"
        with open(entity_file, "w") as f:
            json.dump(result, f, indent=2)

        # Small delay to avoid overwhelming the server
        await asyncio.sleep(0.2)

    # Save complete results
    with open(output_dir / "complete_discovery.json", "w") as f:
        json.dump(results, f, indent=2)

    # Generate summary
    print("\n" + "=" * 80)
    print("DISCOVERY COMPLETE - SUMMARY")
    print("=" * 80)

    total = len(results)
    with_metadata = sum(1 for r in results if r["metadata"])
    with_data = sum(1 for r in results if r["recordCount"] > 0)

    print(f"\nTotal entities discovered: {total}")
    print(f"Entities with metadata: {with_metadata}/{total}")
    print(f"Entities with data: {with_data}/{total}")

    # Breakdown by scope
    by_scope = {}
    for r in results:
        scope = r["apiScope"]
        if scope not in by_scope:
            by_scope[scope] = {"total": 0, "with_data": 0, "total_records": 0}
        by_scope[scope]["total"] += 1
        if r["recordCount"] > 0:
            by_scope[scope]["with_data"] += 1
        by_scope[scope]["total_records"] += r["recordCount"]

    print("\nBreakdown by scope:")
    for scope, stats in sorted(by_scope.items()):
        print(
            f"  {scope:15s}: {stats['total']:3d} entities, "
            f"{stats['with_data']:3d} with data, "
            f"{stats['total_records']:4d} total records"
        )

    print(f"\n✓ Complete discovery saved to {output_dir / 'complete_discovery.json'}")
    print(f"✓ Individual entity files saved to {output_dir / 'entity_*.json'}")


async def main():
    """Main entry point."""
    print("=" * 80)
    print("FirstShift API Gateway - Complete Discovery")
    print("=" * 80)
    print("\nThis script will:")
    print("  1. List all available API endpoints")
    print("  2. Get metadata for each endpoint")
    print("  3. Query sample data from each endpoint")
    print("\n" + "=" * 80 + "\n")

    # Create output directory
    output_dir = Path(__file__).parent.parent / "discovery_results"
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir}\n")

    # Authenticate
    print("Authenticating...")
    token = await authenticate()

    # Discover all entities
    await discover_all_entities(token, output_dir)

    print("\n" + "=" * 80)
    print("✅ Discovery complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
