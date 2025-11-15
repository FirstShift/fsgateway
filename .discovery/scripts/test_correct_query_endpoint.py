#!/usr/bin/env python3
"""Test the correct query endpoint format discovered from documentation.

The documentation shows the query endpoint is:
POST /api/v1/{apiScope}/{entityName}/query

NOT:
POST /api/v1/query/{apiUrl}

This script tests the corrected endpoint format.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

# Configuration from environment
BASE_URL = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
USERNAME = os.getenv("FSGW_USERNAME", "arun.lobo@firstshift.ai")
PASSWORD = os.getenv("FSGW_PASSWORD", "FirstShift@2024")
TENANT_ID = int(os.getenv("FSGW_TENANT_ID", "7"))


async def authenticate() -> str:
    """Authenticate and get access token."""
    if not USERNAME or not PASSWORD:
        raise ValueError("Please set FSGW_USERNAME and FSGW_PASSWORD environment variables")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"userName": USERNAME, "password": PASSWORD, "tenantId": TENANT_ID},
            timeout=30.0,
        )

        if response.status_code != 200:
            print(f"Auth failed with status {response.status_code}")
            print(f"Response: {response.text}")
            response.raise_for_status()

        data = response.json()
        return data["data"]["access-token"]


async def query_entity(token: str, api_url: str, limit: int = 5) -> dict:
    """Query an entity using the CORRECT endpoint format.

    Args:
        token: Access token
        api_url: The apiUrl from API #1 (e.g., "ops/auditTrail")
        limit: Number of records to retrieve

    Returns:
        Response data
    """
    # Split apiUrl into scope and entity name
    # e.g., "ops/auditTrail" -> scope="ops", entity="auditTrail"
    parts = api_url.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid apiUrl format: {api_url}")

    scope, entity = parts

    # Construct the CORRECT endpoint
    endpoint = f"{BASE_URL}/api/v1/{scope}/{entity}/query"

    # Build query payload
    payload = {
        "limit": limit,
        "page": 1,
    }

    print(f"\n{'='*80}")
    print(f"Testing: {api_url}")
    print(f"Endpoint: {endpoint}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*80}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                endpoint,
                headers={
                    "access-token": token,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30.0,
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS!")
                print(f"Response keys: {list(data.keys())}")
                if "data" in data and isinstance(data["data"], list):
                    print(f"Records returned: {len(data['data'])}")
                    if data["data"]:
                        print(f"Sample record keys: {list(data['data'][0].keys())}")
                return data
            else:
                print(f"❌ FAILED: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Error text: {response.text[:500]}")
                return None

        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            return None


async def main():
    """Test the corrected query endpoint format."""
    print("=" * 80)
    print("Testing CORRECTED Query Endpoint Format")
    print("=" * 80)

    # Authenticate
    print("\n1. Authenticating...")
    token = await authenticate()
    print(f"✅ Got access token: {token[:20]}...")

    # Test entities from different scopes
    test_entities = [
        "ops/auditTrail",
        "config/configBusinessCalendar",
        "metadata/globalRbacObjects",
        "data/dimensionMaster",
        "rbac/rbacPermissionGroups",
    ]

    print(f"\n2. Testing {len(test_entities)} entities...")

    results = []
    for api_url in test_entities:
        result = await query_entity(token, api_url, limit=3)
        results.append({
            "api_url": api_url,
            "success": result is not None,
            "data": result,
        })
        # Small delay between requests
        await asyncio.sleep(0.5)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\n✅ Successful: {len(successful)}/{len(results)}")
    for r in successful:
        record_count = len(r["data"]["data"]) if r["data"] and "data" in r["data"] else 0
        print(f"  - {r['api_url']}: {record_count} records")

    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(results)}")
        for r in failed:
            print(f"  - {r['api_url']}")

    # Save results
    output_file = Path(__file__).parent.parent / "query_test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📄 Full results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
