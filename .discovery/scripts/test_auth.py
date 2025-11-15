"""
Test authentication with the updated models.
"""

import asyncio
import json
import os

from fsgw.auth.models import AuthOutput, LoginRequest
from fsgw.client import FSGWClient


async def test_auth():
    """Test authentication."""
    gateway_url = os.getenv("FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai")
    tenant_id = int(os.getenv("FSGW_TENANT_ID", "7"))
    username = os.getenv("FSGW_USERNAME", "")
    password = os.getenv("FSGW_PASSWORD", "")

    if not username or not password:
        print("Error: FSGW_USERNAME and FSGW_PASSWORD must be set")
        return

    print(f"Testing authentication")
    print(f"Gateway: {gateway_url}")
    print(f"Tenant: {tenant_id}")
    print(f"Username: {username}")
    print()

    try:
        async with FSGWClient(
            gateway_url=gateway_url,
            tenant_id=tenant_id,
            username=username,
            password=password,
        ) as client:
            # Try to trigger authentication
            print("Triggering lazy authentication...")
            # This should work now with the fixed auth models

            # Check if authenticated
            if client.auth_token:
                print("✓ Authentication successful!")
                print(f"  Access token (first 50 chars): {client.auth_token.access_token[:50]}...")
                print(f"  Has refresh token: {bool(client.auth_token.refresh_token)}")

                if client.user_info:
                    print(f"  User ID: {client.user_info.id}")
                    print(f"  Username: {client.user_info.username}")

                print(f"  Roles: {client.roles}")
            else:
                print("✗ Authentication failed - no token")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_auth())
