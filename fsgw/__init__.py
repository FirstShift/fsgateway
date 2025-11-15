"""
fsgw - FirstShift API Gateway SDK

Python SDK for FirstShift Metadata Query and Dynamic Entity Access API.
"""

__version__ = "0.1.0"

from fsgw.client import FSGWClient
from fsgw.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    EntityNotFoundError,
    FSGWException,
    MetadataError,
    NetworkError,
    QueryError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from fsgw.models.endpoints import EndpointEntity, EndpointsResponse
from fsgw.models.metadata import FieldMetadata, FieldType, MetadataResponse
from fsgw.models.query import (
    FilterCriteria,
    FilterOperation,
    LogicalOperator,
    QueryRequest,
    QueryResponse,
    SortDirection,
    SortOrder,
)
from fsgw.models.responses import (
    BaseResponse,
    DataResponse,
    ErrorResponse,
    ListResponse,
    PaginatedResponse,
    SingleResponse,
)

__all__ = [
    # Main client
    "FSGWClient",
    # Exceptions
    "FSGWException",
    "AuthenticationError",
    "AuthorizationError",
    "APIError",
    "ValidationError",
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    "EntityNotFoundError",
    "MetadataError",
    "QueryError",
    "ConfigurationError",
    # Response models
    "BaseResponse",
    "DataResponse",
    "ErrorResponse",
    "ListResponse",
    "SingleResponse",
    "PaginatedResponse",
    # Entity models
    "EndpointEntity",
    "EndpointsResponse",
    # Metadata models
    "FieldMetadata",
    "FieldType",
    "MetadataResponse",
    # Query models
    "QueryRequest",
    "QueryResponse",
    "FilterCriteria",
    "FilterOperation",
    "LogicalOperator",
    "SortOrder",
    "SortDirection",
]
