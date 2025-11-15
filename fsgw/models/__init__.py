"""Data models for FSGW SDK."""

from fsgw.models.endpoints import EndpointEntity, EndpointGroup, EndpointsResponse
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
    # Response models
    "BaseResponse",
    "DataResponse",
    "ErrorResponse",
    "ListResponse",
    "PaginatedResponse",
    "SingleResponse",
    # Endpoint models
    "EndpointGroup",
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
