"""
Test script for Phase 2 FSGWClient implementation.

This script tests the complete client infrastructure:
- Authentication with token caching
- API #1: Discovery (list entities)
- API #2: Metadata (get field information)
- API #3: Query (retrieve data)
"""

import asyncio
import os
from pathlib import Path

from fsgw import FSGWClient, QueryRequest


async def main():
    """Test Phase 2 client implementation."""
    # Load credentials from environment
    gateway_url = os.getenv(
        "FSGW_GATEWAY_URL", "https://dev-cloudgateway.firstshift.ai"
    )
    username = os.getenv("FSGW_USERNAME")
    password = os.getenv("FSGW_PASSWORD")
    tenant_id = int(os.getenv("FSGW_TENANT_ID", "7"))

    if not username or not password:
        print("ERROR: FSGW_USERNAME and FSGW_PASSWORD must be set")
        return

    print("=" * 80)
    print("Phase 2 Client Test")
    print("=" * 80)
    print(f"Gateway URL: {gateway_url}")
    print(f"Username: {username}")
    print(f"Tenant ID: {tenant_id}")
    print()

    # Create client
    async with FSGWClient(
        gateway_url=gateway_url,
        username=username,
        password=password,
        tenant_id=tenant_id,
    ) as client:
        # Test 1: Authentication (happens automatically)
        print("Test 1: Authentication")
        print("-" * 80)
        try:
            # This will trigger authentication on first call
            entities = await client.list_apis(use_cache=False)
            print(f"✓ Authentication successful")
            print(f"  Authenticated: {client.is_authenticated}")
            print(f"  User: {client.current_user}")
            print(f"  Roles: {client.current_roles}")
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return
        print()

        # Test 2: API #1 - Discovery
        print("Test 2: API #1 - Discovery")
        print("-" * 80)
        try:
            print(f"  Found {len(entities)} entities")

            # Group by scope
            by_scope = {}
            for entity in entities:
                if entity.api_scope not in by_scope:
                    by_scope[entity.api_scope] = []
                by_scope[entity.api_scope].append(entity)

            print(f"  Scopes: {list(by_scope.keys())}")
            for scope, scope_entities in by_scope.items():
                print(f"    {scope}: {len(scope_entities)} entities")

            # Test get_api_info
            audit_trail = await client.get_api_info("ops/auditTrail")
            print(f"  Audit Trail info:")
            print(f"    Scope: {audit_trail.api_scope}")
            print(f"    URL: {audit_trail.api_url}")
            print(f"    Name: {audit_trail.external_api_name}")
            print(f"    Description: {audit_trail.description}")
        except Exception as e:
            print(f"✗ Discovery failed: {e}")
            return
        print()

        # Test 3: API #2 - Metadata
        print("Test 3: API #2 - Metadata")
        print("-" * 80)
        try:
            metadata = await client.get_metadata("ops/auditTrail")
            print(f"  Found {len(metadata)} fields")

            # Get primary keys
            pk_fields = await client.get_primary_keys("ops/auditTrail")
            print(f"  Primary keys: {pk_fields}")

            # Get field types
            field_types = await client.get_field_types("ops/auditTrail")
            print(f"  Field types: {len(field_types)} fields")

            # Show first 5 fields
            print(f"  First 5 fields:")
            for field in metadata[:5]:
                nullable = "NULL" if field.field_can_be_null else "NOT NULL"
                pk = "PK" if field.is_primary_key else ""
                print(f"    {field.field_name}: {field.type} {nullable} {pk}")
        except Exception as e:
            print(f"✗ Metadata retrieval failed: {e}")
            return
        print()

        # Test 4: API #3 - Query (simple)
        print("Test 4: API #3 - Simple Query")
        print("-" * 80)
        try:
            query = QueryRequest().limit(5)
            results = await client.query("ops/auditTrail", query)
            print(f"  Retrieved {results.total} records")
            print(f"  First record keys: {list(results.results[0].keys()) if results.results else []}")
        except Exception as e:
            print(f"✗ Simple query failed: {e}")
            return
        print()

        # Test 5: API #3 - Query with filters
        print("Test 5: API #3 - Query with Filters")
        print("-" * 80)
        try:
            query = (
                QueryRequest()
                .add_filter("tenantId", "=", tenant_id)
                .add_sort("auditId", "DESC")
                .limit(10)
            )
            results = await client.query("ops/auditTrail", query)
            print(f"  Retrieved {results.total} records for tenant {tenant_id}")
            if results.results:
                first = results.results[0]
                print(f"  First record:")
                print(f"    Audit ID: {first.get('auditId')}")
                print(f"    Event Name: {first.get('eventName')}")
                print(f"    Tenant ID: {first.get('tenantId')}")
                print(f"    Created At: {first.get('createdAt')}")
        except Exception as e:
            print(f"✗ Filtered query failed: {e}")
            return
        print()

        # Test 6: Query with filters helper
        print("Test 6: Query with Filters Helper")
        print("-" * 80)
        try:
            results = await client.query_with_filters(
                "ops/auditTrail",
                [
                    ("tenantId", "=", tenant_id),
                    ("eventName", "LIKE", "CREATE%"),
                ],
            )
            print(f"  Retrieved {results.total} CREATE events")
        except Exception as e:
            print(f"✗ Filter helper failed: {e}")
            return
        print()

        # Test 7: Cache functionality
        print("Test 7: Cache Functionality")
        print("-" * 80)
        try:
            # First call (from cache)
            import time
            start = time.time()
            entities1 = await client.list_apis(use_cache=True)
            elapsed1 = time.time() - start
            print(f"  Cached call: {elapsed1:.3f}s")

            # Clear cache and call again
            client.clear_apis_cache()
            start = time.time()
            entities2 = await client.list_apis(use_cache=False)
            elapsed2 = time.time() - start
            print(f"  Fresh call: {elapsed2:.3f}s")

            print(f"  Cache speedup: {elapsed2/elapsed1:.1f}x")
        except Exception as e:
            print(f"✗ Cache test failed: {e}")
            return
        print()

        print("=" * 80)
        print("All Phase 2 tests passed! ✓")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
