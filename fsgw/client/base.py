"""
Base HTTP client for FSGW SDK.

Provides HTTP operations with connection pooling, retry logic, and error handling.
"""

import asyncio
from typing import Any

import httpx

from fsgw.exceptions import (
    APIError,
    NetworkError,
    RateLimitError,
    TimeoutError as FSGWTimeoutError,
)


class BaseClient:
    """
    Base HTTP client with connection pooling and retry logic.

    Features:
    - Connection pooling for better performance
    - Automatic retries with exponential backoff
    - Timeout configuration
    - Error handling and conversion to SDK exceptions
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
    ):
        """
        Initialize base HTTP client.

        Args:
            base_url: Base URL for all requests
            timeout: Default timeout in seconds
            max_retries: Maximum number of retry attempts
            max_connections: Maximum number of concurrent connections
            max_keepalive_connections: Maximum number of keep-alive connections
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Connection limits for connection pooling
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

        # HTTP client instance
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client.

        Returns:
            Configured httpx AsyncClient
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=self._limits,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client and cleanup connections."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "BaseClient":
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Context manager exit."""
        await self.close()

    def _should_retry(self, attempt: int, exception: Exception) -> bool:
        """
        Determine if request should be retried.

        Args:
            attempt: Current retry attempt number (0-indexed)
            exception: Exception that occurred

        Returns:
            True if should retry
        """
        # Don't retry if we've exhausted attempts
        if attempt >= self.max_retries:
            return False

        # Retry on network errors
        if isinstance(exception, (httpx.NetworkError, httpx.ConnectError)):
            return True

        # Retry on timeout
        if isinstance(exception, httpx.TimeoutException):
            return True

        # Retry on 5xx server errors
        if isinstance(exception, httpx.HTTPStatusError):
            if exception.response.status_code >= 500:
                return True

        # Retry on rate limit (429)
        if isinstance(exception, httpx.HTTPStatusError):
            if exception.response.status_code == 429:
                return True

        return False

    def _get_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff.

        Args:
            attempt: Current retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: 1s, 2s, 4s, 8s, ...
        base_delay = 1.0
        max_delay = 30.0
        delay = min(base_delay * (2**attempt), max_delay)
        return delay

    async def _handle_response_error(self, response: httpx.Response) -> None:
        """
        Convert HTTP errors to SDK exceptions.

        Args:
            response: HTTP response

        Raises:
            APIError: For 4xx and 5xx errors
            RateLimitError: For 429 rate limit errors
        """
        try:
            data = response.json()
        except Exception:
            data = {"message": response.text}

        # Rate limit error
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message="Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )

        # API error
        message = data.get("message", f"HTTP {response.status_code}")
        raise APIError(
            message=message,
            status_code=response.status_code,
            response_data=data,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path (relative to base_url)
            headers: Optional request headers
            params: Optional query parameters
            json: Optional JSON body
            timeout: Optional timeout override

        Returns:
            HTTP response

        Raises:
            APIError: For API errors
            NetworkError: For network errors
            TimeoutError: For timeout errors
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        request_timeout = timeout or self.timeout

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=request_timeout,
                )

                # Raise for HTTP errors (4xx, 5xx)
                if response.status_code >= 400:
                    await self._handle_response_error(response)

                return response

            except httpx.TimeoutException as e:
                if not self._should_retry(attempt, e):
                    raise FSGWTimeoutError(
                        f"Request timeout after {request_timeout}s",
                        timeout_seconds=request_timeout,
                    ) from e

            except httpx.NetworkError as e:
                if not self._should_retry(attempt, e):
                    raise NetworkError(f"Network error: {e}") from e

            except httpx.HTTPStatusError as e:
                if not self._should_retry(attempt, e):
                    raise

            # Wait before retry with exponential backoff
            if attempt < self.max_retries:
                delay = self._get_retry_delay(attempt)
                await asyncio.sleep(delay)

        # Should never reach here, but just in case
        raise NetworkError("Max retries exceeded")

    async def get(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """
        Make GET request.

        Args:
            path: Request path
            headers: Optional headers
            params: Optional query parameters
            timeout: Optional timeout

        Returns:
            HTTP response
        """
        return await self.request(
            "GET", path, headers=headers, params=params, timeout=timeout
        )

    async def post(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """
        Make POST request.

        Args:
            path: Request path
            headers: Optional headers
            params: Optional query parameters
            json: Optional JSON body
            timeout: Optional timeout

        Returns:
            HTTP response
        """
        return await self.request(
            "POST", path, headers=headers, params=params, json=json, timeout=timeout
        )

    async def put(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """
        Make PUT request.

        Args:
            path: Request path
            headers: Optional headers
            params: Optional query parameters
            json: Optional JSON body
            timeout: Optional timeout

        Returns:
            HTTP response
        """
        return await self.request(
            "PUT", path, headers=headers, params=params, json=json, timeout=timeout
        )

    async def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """
        Make DELETE request.

        Args:
            path: Request path
            headers: Optional headers
            params: Optional query parameters
            timeout: Optional timeout

        Returns:
            HTTP response
        """
        return await self.request(
            "DELETE", path, headers=headers, params=params, timeout=timeout
        )
