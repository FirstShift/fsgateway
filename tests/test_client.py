"""
Basic tests for FSGW client.

These are placeholder tests. Actual tests will depend on the API implementation.
"""

import pytest

from fsgw.client import FSGWClient


def test_client_initialization():
    """Test that client can be initialized with valid config."""
    client = FSGWClient(
        gateway_url="https://dev-cloudgateway.firstshift.ai",
        tenant_id=7,
        username="test@example.com",
        password="password123",
    )

    assert client.gateway_url == "https://dev-cloudgateway.firstshift.ai"
    assert client.tenant_id == 7
    assert client.username == "test@example.com"


def test_client_url_validation():
    """Test that invalid URLs are rejected."""
    with pytest.raises(ValueError, match="must start with http"):
        FSGWClient(
            gateway_url="invalid-url",
            tenant_id=7,
            username="test@example.com",
            password="password123",
        )


def test_client_url_normalization():
    """Test that URLs are normalized correctly."""
    client = FSGWClient(
        gateway_url="https://example.com/",
        tenant_id=7,
        username="test@example.com",
        password="password123",
    )

    # Trailing slash should be removed
    assert client.gateway_url == "https://example.com"


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test that client works as async context manager."""
    async with FSGWClient(
        gateway_url="https://dev-cloudgateway.firstshift.ai",
        tenant_id=7,
        username="test@example.com",
        password="password123",
    ) as client:
        assert client is not None
        assert client._http_client is not None
