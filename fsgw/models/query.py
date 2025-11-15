"""
Models for API #3 - Query Data for Any Entity.

Supports fully generic querying with filters, sorting, pagination, and optional projections.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class FilterOperation(str, Enum):
    """Supported filter operations."""

    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"


class LogicalOperator(str, Enum):
    """Logical operators for combining filters."""

    AND = "AND"
    OR = "OR"


class SortDirection(str, Enum):
    """Sort direction."""

    ASC = "ASC"
    DESC = "DESC"


class FilterCriteria(BaseModel):
    """
    A single filter criterion.

    Matches the actual API request structure.
    """

    key: str = Field(..., description="Field name to filter on")
    operation: str = Field(..., description="Filter operation (=, !=, >, <, LIKE, IN, etc.)")
    value: Any = Field(..., description="Value to filter by")
    prefix_operation: str | None = Field(
        default=None,
        alias="prefixOperation",
        description="Logical operator to combine with previous filter (AND, OR)",
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True
        use_enum_values = True

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate that operation is supported."""
        try:
            FilterOperation(v)
        except ValueError:
            # Allow the operation anyway - API might support more
            pass
        return v

    @field_validator("prefix_operation")
    @classmethod
    def validate_prefix_operation(cls, v: str | None) -> str | None:
        """Validate logical operator."""
        if v is None:
            return v
        try:
            LogicalOperator(v)
        except ValueError:
            # Allow it anyway
            pass
        return v


class SortOrder(BaseModel):
    """
    Sort order specification.

    Matches the actual API request structure.
    """

    column: str = Field(..., description="Field name to sort by")
    sort_order: str = Field(
        ...,
        alias="sortOrder",
        description="Sort direction (ASC or DESC)",
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort direction."""
        v_upper = v.upper()
        try:
            SortDirection(v_upper)
            return v_upper
        except ValueError:
            return v


class QueryRequest(BaseModel):
    """
    Request for querying entity data.

    Matches the actual API request structure from documentation.
    """

    criteria_list: list[FilterCriteria] = Field(
        default_factory=list,
        alias="criteriaList",
        description="List of filter criteria (empty = no filters)",
    )
    order_by_list: list[SortOrder] = Field(
        default_factory=list,
        alias="orderByList",
        description="List of sort orders (empty = no sorting)",
    )
    select_fields_list: list[str] = Field(
        default_factory=list,
        alias="selectFieldsList",
        description="Fields to include in response (empty = all fields)",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip for pagination",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of records to return",
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True

    @property
    def page(self) -> int:
        """Calculate page number from offset and limit."""
        return (self.offset // self.limit) + 1 if self.limit > 0 else 1

    def add_filter(
        self,
        field: str,
        operation: str | FilterOperation,
        value: Any,
        logical_op: str | LogicalOperator | None = None,
    ) -> "QueryRequest":
        """
        Add a filter criterion (fluent interface).

        Args:
            field: Field name to filter on
            operation: Filter operation
            value: Value to filter by
            logical_op: Logical operator (AND/OR) if not first filter

        Returns:
            Self for chaining
        """
        op_str = operation.value if isinstance(operation, FilterOperation) else operation
        prefix = None
        if self.criteria_list and logical_op is not None:
            prefix = logical_op.value if isinstance(logical_op, LogicalOperator) else logical_op

        self.criteria_list.append(
            FilterCriteria(
                key=field,
                operation=op_str,
                value=value,
                prefix_operation=prefix,
            )
        )
        return self

    def add_sort(
        self, field: str, direction: str | SortDirection = SortDirection.ASC
    ) -> "QueryRequest":
        """
        Add a sort order (fluent interface).

        Args:
            field: Field name to sort by
            direction: Sort direction (ASC or DESC)

        Returns:
            Self for chaining
        """
        dir_str = direction.value if isinstance(direction, SortDirection) else direction
        self.order_by_list.append(SortOrder(column=field, sort_order=dir_str))
        return self

    def select_fields(self, *fields: str) -> "QueryRequest":
        """
        Set fields to select (fluent interface).

        Args:
            *fields: Field names to include in response

        Returns:
            Self for chaining
        """
        self.select_fields_list = list(fields)
        return self

    def paginate(self, page: int = 1, page_size: int = 100) -> "QueryRequest":
        """
        Set pagination parameters (fluent interface).

        Args:
            page: Page number (1-indexed)
            page_size: Number of records per page

        Returns:
            Self for chaining
        """
        self.limit = page_size
        self.offset = (page - 1) * page_size
        return self


class QueryResponse(BaseModel):
    """
    Response from API #3 - Query Data for Any Entity.

    Contains query results.
    """

    data: list[dict[str, Any]] | None = Field(
        default=None, description="Query results as list of records"
    )

    def get_records(self) -> list[dict[str, Any]]:
        """Get records, returning empty list if None."""
        return self.data if self.data is not None else []

    @property
    def count(self) -> int:
        """Get number of records returned."""
        return len(self.get_records())

    def __iter__(self):
        """Allow iteration over records."""
        return iter(self.get_records())

    def __len__(self) -> int:
        """Get number of records."""
        return self.count

    def __getitem__(self, index: int) -> dict[str, Any]:
        """Get record by index."""
        return self.get_records()[index]
