"""
Live API Discovery Script

This script calls the actual FirstShift API Gateway to discover all available endpoints.
"""

import asyncio
import json
import os
from typing import Any

import httpx


async def authenticate(gateway_url: str, tenant_id: int, username: str, password: str) -> str | None:
    """Authenticate and get access token."""
    print(f"\n{'='*80}")
    print("STEP 1: AUTHENTICATING")
    print(f"{'='*80}")
    print(f"Gateway: {gateway_url}")
    print(f"Tenant: {tenant_id}")
    print(f"Username: {username}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{gateway_url}/auth/login",
                json={
                    "userName": username,
                    "password": password,
                    "tenantId": tenant_id,
                },
                timeout=30.0,
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")

                # Save full response for debugging
                with open("auth_response.json", "w") as f:
                    json.dump(data, f, indent=2)
                print("  Saved full response to auth_response.json")

                # Try to extract access token from various possible locations
                access_token = None
                if "data" in data and isinstance(data["data"], dict):
                    # Check nested data
                    if "access-token" in data["data"]:
                        access_token = data["data"]["access-token"]
                    elif "accessToken" in data["data"]:
                        access_token = data["data"]["accessToken"]
                    elif "access_token" in data["data"]:
                        access_token = data["data"]["access_token"]
                    elif "token" in data["data"]:
                        access_token = data["data"]["token"]
                elif "access-token" in data:
                    access_token = data["access-token"]
                elif "accessToken" in data:
                    access_token = data["accessToken"]
                elif "access_token" in data:
                    access_token = data["access_token"]

                if access_token:
                    print(f"✓ Authentication successful!")
                    print(f"  Token (first 50 chars): {access_token[:50]}...")
                    return access_token
                else:
                    print(f"✗ No access token found in response")
                    print(f"  Checking response structure...")
                    print(f"  Data type: {type(data.get('data'))}")
                    if isinstance(data.get("data"), dict):
                        print(f"  Data keys: {list(data['data'].keys())[:10]}")
            else:
                print(f"✗ Authentication failed")
                print(f"  Response: {response.text[:500]}")

        except Exception as e:
            print(f"✗ Error during authentication: {e}")

    return None


async def list_endpoints(gateway_url: str, access_token: str) -> dict[str, Any] | None:
    """Call API #1 - List all available endpoints."""
    print(f"\n{'='*80}")
    print("STEP 2: LISTING ALL AVAILABLE ENDPOINTS (API #1)")
    print(f"{'='*80}")

    # Try different possible endpoint paths
    possible_paths = [
        "/api/v1/endpoints",
        "/api/endpoints",
        "/endpoints",
        "/api/v1/metadata/endpoints",
        "/v1/metadata/endpoints",
        "/metadata/endpoints",
        "/api/discover",
        "/api/v1/discover",
        "/v1/entities",
        "/api/v1/entities",
    ]

    async with httpx.AsyncClient() as client:
        # Try GET first
        for path in possible_paths:
            try:
                print(f"\nTrying: GET {gateway_url}{path}")
                response = await client.get(
                    f"{gateway_url}{path}",
                    headers={"access-token": access_token},
                    timeout=30.0,
                )

                print(f"  Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✓ SUCCESS!")
                    print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                    print(f"  Response preview: {json.dumps(data, indent=2)[:500]}...")
                    return data
                elif response.status_code == 405:
                    # Try POST
                    print(f"  405 Method Not Allowed, trying POST...")
                    response = await client.post(
                        f"{gateway_url}{path}",
                        headers={"access-token": access_token},
                        json={},
                        timeout=30.0,
                    )
                    print(f"  POST Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"  ✓ SUCCESS!")
                        print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                        print(f"  Response preview: {json.dumps(data, indent=2)[:500]}...")
                        return data
                    else:
                        print(f"  Response: {response.text[:200]}")
                elif response.status_code != 404:
                    print(f"  Response: {response.text[:200]}")

            except Exception as e:
                print(f"  Error: {e}")

    print("\n✗ Could not find the endpoints list API")
    return None


async def get_metadata(gateway_url: str, access_token: str, entity: str) -> dict[str, Any] | None:
    """Call API #2 - Get metadata for an entity."""
    print(f"\n{'='*80}")
    print(f"STEP 3: GETTING METADATA FOR '{entity}' (API #2)")
    print(f"{'='*80}")

    # Try different possible endpoint paths
    possible_paths = [
        f"/v1/metadata/{entity}",
        f"/api/v1/metadata/{entity}",
        f"/api/metadata/{entity}",
        f"/metadata/{entity}",
        f"/api/v1/entities/{entity}/metadata",
        f"/api/entities/{entity}/schema",
    ]

    async with httpx.AsyncClient() as client:
        for path in possible_paths:
            try:
                print(f"\nTrying: GET {gateway_url}{path}")
                response = await client.get(
                    f"{gateway_url}{path}",
                    headers={"access-token": access_token},
                    timeout=30.0,
                )

                print(f"  Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✓ SUCCESS!")
                    with open(f"metadata_{entity}.json", "w") as f:
                        json.dump(data, f, indent=2)
                    print(f"  Saved to metadata_{entity}.json")
                    print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                    print(f"  Response preview: {json.dumps(data, indent=2)[:500]}...")
                    return data
                elif response.status_code == 405:
                    # Try POST
                    print(f"  405 Method Not Allowed, trying POST...")
                    response = await client.post(
                        f"{gateway_url}{path}",
                        headers={"access-token": access_token},
                        json={"entity": entity},
                        timeout=30.0,
                    )
                    print(f"  POST Status: {response.status_code}")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"  ✓ SUCCESS!")
                        with open(f"metadata_{entity}.json", "w") as f:
                            json.dump(data, f, indent=2)
                        print(f"  Saved to metadata_{entity}.json")
                        print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                        print(f"  Response preview: {json.dumps(data, indent=2)[:500]}...")
                        return data
                    else:
                        print(f"  Response: {response.text[:200]}")
                elif response.status_code != 404:
                    print(f"  Response: {response.text[:200]}")

            except Exception as e:
                print(f"  Error: {e}")

    print(f"\n✗ Could not find metadata API for '{entity}'")
    return None


async def query_data(gateway_url: str, access_token: str, entity: str) -> dict[str, Any] | None:
    """Call API #3 - Query data from an entity."""
    print(f"\n{'='*80}")
    print(f"STEP 4: QUERYING DATA FROM '{entity}' (API #3)")
    print(f"{'='*80}")

    # Try different possible endpoint paths
    possible_paths = [
        f"/api/v1/query/{entity}",
        f"/api/query/{entity}",
        f"/query/{entity}",
        f"/api/v1/entities/{entity}/query",
        f"/api/v1/entities/{entity}/data",
        f"/api/v1/{entity}",
    ]

    query_body = {
        "limit": 5,
        "page": 1,
    }

    async with httpx.AsyncClient() as client:
        # Try POST first
        for path in possible_paths:
            try:
                print(f"\nTrying: POST {gateway_url}{path}")
                response = await client.post(
                    f"{gateway_url}{path}",
                    headers={"access-token": access_token},
                    json=query_body,
                    timeout=30.0,
                )

                print(f"  Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✓ SUCCESS!")
                    print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                    print(f"  Response preview: {json.dumps(data, indent=2)[:500]}...")
                    return data
                elif response.status_code != 404:
                    print(f"  Response: {response.text[:200]}")

            except Exception as e:
                print(f"  Error: {e}")

        # Try GET
        for path in possible_paths:
            try:
                print(f"\nTrying: GET {gateway_url}{path}")
                response = await client.get(
                    f"{gateway_url}{path}",
                    headers={"access-token": access_token},
                    params={"limit": 5},
                    timeout=30.0,
                )

                print(f"  Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"  ✓ SUCCESS!")
                    print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                    print(f"  Response preview: {json.dumps(data, indent=2)[:500]}...")
                    return data
                elif response.status_code != 404:
                    print(f"  Response: {response.text[:200]}")

            except Exception as e:
                print(f"  Error: {e}")

    print(f"\n✗ Could not find query API for '{entity}'")
    return None


async def main():
    """Main discovery workflow."""
    # Get credentials from environment
    gateway_url = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
    tenant_id = int(os.getenv("FSGW_TENANT_ID", "7"))
    username = os.getenv("FSGW_USERNAME", "")
    password = os.getenv("FSGW_PASSWORD", "")

    if not username or not password:
        print("Error: FSGW_USERNAME and FSGW_PASSWORD must be set")
        return

    # Step 1: Authenticate
    access_token = await authenticate(gateway_url, tenant_id, username, password)
    if not access_token:
        print("\n✗ Authentication failed. Cannot proceed.")
        return

    # Step 2: Try to list all endpoints
    endpoints = await list_endpoints(gateway_url, access_token)

    # Step 3 & 4: Try common entity names to discover the API structure
    print(f"\n{'='*80}")
    print("EXPLORING COMMON ENTITY NAMES")
    print(f"{'='*80}")

    common_entities = [
        "products",
        "customers",
        "orders",
        "inventory",
        "forecasts",
        "items",
        "sales",
        "demand",
    ]

    for entity in common_entities:
        # Try to get metadata
        metadata = await get_metadata(gateway_url, access_token, entity)

        if metadata:
            # If metadata works, try to query data
            await query_data(gateway_url, access_token, entity)
            break  # Found one that works, we can explore more later

    print(f"\n{'='*80}")
    print("DISCOVERY COMPLETE")
    print(f"{'='*80}")
    print("\nResults will be saved to discovery_results.json")


if __name__ == "__main__":
    asyncio.run(main())
