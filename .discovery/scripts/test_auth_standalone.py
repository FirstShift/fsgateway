"""
Standalone authentication test - no package import needed.
"""

import asyncio
import json
import os
import sys

import httpx


async def test_auth():
    """Test authentication."""
    gateway_url = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
    tenant_id = int(os.getenv("FSGW_TENANT_ID", "7"))
    username = os.getenv("FSGW_USERNAME", "")
    password = os.getenv("FSGW_PASSWORD", "")

    if not username or not password:
        print("Error: FSGW_USERNAME and FSGW_PASSWORD must be set")
        return False

    print("="*80)
    print("TESTING AUTHENTICATION")
    print("="*80)
    print(f"Gateway: {gateway_url}")
    print(f"Tenant: {tenant_id}")
    print(f"Username: {username}")
    print()

    async with httpx.AsyncClient() as client:
        try:
            # Test authentication
            print("Sending POST /auth/login...")
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

                # Save response
                with open("auth_response.json", "w") as f:
                    json.dump(data, f, indent=2)

                # Extract token
                if "data" in data and isinstance(data["data"], dict):
                    access_token = data["data"].get("access-token")
                    refresh_token = data["data"].get("refresh-token")

                    if access_token:
                        print("✓ Authentication SUCCESSFUL!")
                        print(f"\n  Access Token (first 50 chars): {access_token[:50]}...")
                        print(f"  Refresh Token: {'Yes' if refresh_token else 'No'}")

                        # Check user data
                        user_data = data["data"].get("userData", {})
                        if user_data:
                            print(f"\n  User ID: {user_data.get('id')}")
                            print(f"  Username: {user_data.get('username')}")
                            print(f"  Email: {user_data.get('email')}")

                        # Check roles
                        roles = data["data"].get("roles", [])
                        if roles:
                            print(f"\n  Roles: {roles}")

                        print(f"\n  Full response saved to auth_response.json")
                        return access_token
                    else:
                        print("✗ No access-token found in response")
                        print(f"  Data keys: {list(data['data'].keys())}")
                else:
                    print("✗ Unexpected response structure")
                    print(f"  Response: {json.dumps(data, indent=2)[:500]}")

            else:
                print(f"✗ Authentication failed: {response.status_code}")
                print(f"  Response: {response.text[:500]}")

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    return False


if __name__ == "__main__":
    token = asyncio.run(test_auth())
    sys.exit(0 if token else 1)
