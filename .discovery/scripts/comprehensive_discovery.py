"""
Comprehensive API Discovery Script

Systematically tests all three APIs and documents the structure.
"""

import asyncio
import json
import os
from typing import Any

import httpx


async def authenticate() -> str:
    """Authenticate and return access token."""
    gateway_url = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
    username = os.getenv("FSGW_USERNAME", "")
    password = os.getenv("FSGW_PASSWORD", "")
    tenant_id = int(os.getenv("FSGW_TENANT_ID", "7"))

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{gateway_url}/auth/login",
            json={"userName": username, "password": password, "tenantId": tenant_id},
            timeout=30.0,
        )
        token = response.json()["data"]["access-token"]
        print("✓ Authenticated\n")
        return token


async def test_api1(token: str) -> list[dict[str, Any]]:
    """API #1 - List all available endpoints."""
    print("=" * 80)
    print("API #1: GET /api/v1/meta/apis")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://dev-cloudgateway.firstshift.ai/api/v1/meta/apis",
            headers={"access-token": token},
            timeout=30,
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            entities = data.get("data", [])

            # Save
            with open("discovered_entities.json", "w") as f:
                json.dump(data, f, indent=2)

            print(f"✓ Found {len(entities)} entities")
            print(f"  Saved to discovered_entities.json")

            # Group by scope
            scopes = {}
            for entity in entities:
                scope = entity.get("apiScope", "unknown")
                if scope not in scopes:
                    scopes[scope] = []
                scopes[scope].append(entity)

            print(f"\nEntity Summary:")
            for scope, ents in sorted(scopes.items()):
                print(f"  {scope}: {len(ents)} entities")

            return entities
        else:
            print(f"✗ Failed: {response.text[:500]}")
            return []


async def test_api2(token: str, api_url: str) -> dict[str, Any] | None:
    """API #2 - Get metadata for a specific entity."""
    print(f"\n{'=' * 80}")
    print(f"API #2: GET /api/v1/meta/{api_url}")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://dev-cloudgateway.firstshift.ai/api/v1/meta/{api_url}",
            headers={"access-token": token},
            timeout=30,
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            fields = data.get("data", [])

            # Save
            safe_name = api_url.replace("/", "_")
            with open(f"metadata_{safe_name}.json", "w") as f:
                json.dump(data, f, indent=2)

            print(f"✓ Found {len(fields)} fields")
            print(f"  Saved to metadata_{safe_name}.json")

            # Show field summary
            print(f"\nField Summary:")
            for field in fields[:10]:
                pk = " [PK]" if field.get("isPrimaryKey") else ""
                nullable = " [NULL]" if field.get("fieldCanBeNull") else ""
                print(f"  {field.get('fieldName')}: {field.get('type')}{pk}{nullable}")

            if len(fields) > 10:
                print(f"  ... and {len(fields) - 10} more fields")

            return data
        else:
            print(f"✗ Failed: {response.text[:500]}")
            return None


async def test_api3(token: str, api_url: str, limit: int = 5) -> dict[str, Any] | None:
    """API #3 - Query data from an entity."""
    print(f"\n{'=' * 80}")
    print(f"API #3: POST /api/v1/query/{api_url}")
    print("=" * 80)

    query_body = {
        "limit": limit,
        "page": 1,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://dev-cloudgateway.firstshift.ai/api/v1/query/{api_url}",
            headers={"access-token": token, "Content-Type": "application/json"},
            json=query_body,
            timeout=30,
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])

            # Save
            safe_name = api_url.replace("/", "_")
            with open(f"query_{safe_name}.json", "w") as f:
                json.dump(data, f, indent=2)

            print(f"✓ Found {len(results)} records")
            print(f"  Saved to query_{safe_name}.json")

            # Show sample data
            if results:
                print(f"\nSample Record (first):")
                first = results[0]
                for key, value in list(first.items())[:10]:
                    print(f"  {key}: {value}")
                if len(first) > 10:
                    print(f"  ... and {len(first) - 10} more fields")

            return data
        else:
            print(f"✗ Failed: {response.text[:500]}")
            return None


async def main():
    """Main discovery workflow."""
    print("=" * 80)
    print("FIRSTSHIFT API GATEWAY - COMPREHENSIVE DISCOVERY")
    print("=" * 80)
    print()

    # Step 1: Authenticate
    token = await authenticate()

    # Step 2: Discover all entities (API #1)
    entities = await test_api1(token)

    if not entities:
        print("\n✗ Could not discover entities. Stopping.")
        return

    # Step 3: Test API #2 and API #3 on a few sample entities
    print(f"\n{'=' * 80}")
    print("TESTING API #2 and API #3 ON SAMPLE ENTITIES")
    print("=" * 80)

    # Pick a few interesting entities to test
    test_entities = []

    # Get one from each scope
    scopes_tested = set()
    for entity in entities:
        scope = entity.get("apiScope", "")
        if scope not in scopes_tested:
            test_entities.append(entity)
            scopes_tested.add(scope)
        if len(test_entities) >= 5:
            break

    for entity in test_entities:
        api_url = entity.get("apiUrl", "")
        scope = entity.get("apiScope", "")
        name = entity.get("externalAPIName", "")
        desc = entity.get("description", "")

        print(f"\n{'#' * 80}")
        print(f"Testing: {name} ({scope})")
        print(f"API URL: {api_url}")
        print(f"Description: {desc}")
        print('#' * 80)

        # Test API #2 (metadata)
        metadata = await test_api2(token, api_url)

        # Test API #3 (query)
        if metadata:
            await test_api3(token, api_url, limit=3)

    print(f"\n{'=' * 80}")
    print("DISCOVERY COMPLETE!")
    print("=" * 80)
    print(f"\nFiles created:")
    print(f"  - discovered_entities.json (all {len(entities)} entities)")
    print(f"  - metadata_*.json (field schemas)")
    print(f"  - query_*.json (sample data)")


if __name__ == "__main__":
    asyncio.run(main())
