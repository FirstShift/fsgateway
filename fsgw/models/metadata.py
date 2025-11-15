"""
Models for API #2 - Get Metadata for Any Entity.

Returns field-level schema information including data types, constraints, and primary keys.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FieldType(str, Enum):
    """
    Supported field data types.

    Based on actual DuckDB/MotherDuck types returned by the API.
    """

    # Numeric types
    INT = "Int"
    INTEGER = "Integer"
    BIGINT = "BigInt"
    FLOAT = "Float"
    DOUBLE = "Double"
    DECIMAL = "Decimal"
    NUMERIC = "Numeric"

    # String types
    STRING = "String"
    VARCHAR = "Varchar"
    TEXT = "Text"

    # Boolean
    BOOLEAN = "Boolean"
    BOOL = "Bool"

    # Date/Time types
    DATE = "Date"
    DATETIME = "DateTime"
    TIMESTAMP = "Timestamp"
    TIME = "Time"

    # Other types
    JSON = "Json"
    UUID = "Uuid"
    BLOB = "Blob"

    @classmethod
    def normalize(cls, type_str: str) -> "FieldType | str":
        """
        Normalize a type string to FieldType enum if recognized.

        Args:
            type_str: Type string from API

        Returns:
            FieldType enum member or original string if not recognized
        """
        try:
            return cls(type_str)
        except ValueError:
            # Return original string for unrecognized types
            return type_str

    def is_numeric(self) -> bool:
        """Check if this is a numeric type."""
        return self in {
            FieldType.INT,
            FieldType.INTEGER,
            FieldType.BIGINT,
            FieldType.FLOAT,
            FieldType.DOUBLE,
            FieldType.DECIMAL,
            FieldType.NUMERIC,
        }

    def is_string(self) -> bool:
        """Check if this is a string type."""
        return self in {FieldType.STRING, FieldType.VARCHAR, FieldType.TEXT}

    def is_temporal(self) -> bool:
        """Check if this is a date/time type."""
        return self in {FieldType.DATE, FieldType.DATETIME, FieldType.TIMESTAMP, FieldType.TIME}


class FieldMetadata(BaseModel):
    """
    Metadata for a single field in an entity.

    Matches the actual API response structure from /api/v1/meta/{scope}/{entity}
    """

    field_name: str = Field(
        ...,
        alias="fieldName",
        description="Field name as it appears in the database",
    )
    type: str = Field(..., description="Data type (Int, String, Boolean, etc.)")
    is_primary_key: bool = Field(
        default=False,
        alias="isPrimaryKey",
        description="Whether this field is part of the primary key",
    )
    is_auto_increment: bool = Field(
        default=False,
        alias="isAutoIncrement",
        description="Whether this field auto-increments",
    )
    field_can_be_null: bool = Field(
        default=True,
        alias="fieldCanbeNull",  # Note: API uses "fieldCanbeNull" (lowercase 'b')
        description="Whether this field can contain NULL values",
    )
    is_unique: bool = Field(
        default=False,
        alias="isUnique",
        description="Whether this field has a unique constraint",
    )
    default_value: Any | None = Field(
        default=None,
        alias="defaultValue",
        description="Default value for this field",
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True

    @property
    def field_type(self) -> FieldType | str:
        """Get normalized field type."""
        return FieldType.normalize(self.type)

    @property
    def is_required(self) -> bool:
        """Check if field is required (not nullable and no default)."""
        return not self.field_can_be_null and self.default_value is None

    @property
    def is_nullable(self) -> bool:
        """Check if field can be null."""
        return self.field_can_be_null

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(by_alias=True)


class MetadataResponse(BaseModel):
    """
    Response from API #2 - Get Metadata for Any Entity.

    Contains complete field schema information for an entity.
    """

    fields: list[FieldMetadata] = Field(
        default_factory=list, description="Field definitions for this entity"
    )

    @property
    def field_count(self) -> int:
        """Get total number of fields."""
        return len(self.fields)

    @property
    def primary_keys(self) -> list[str]:
        """Get list of primary key field names."""
        return [f.field_name for f in self.fields if f.is_primary_key]

    @property
    def required_fields(self) -> list[str]:
        """Get list of required field names."""
        return [f.field_name for f in self.fields if f.is_required]

    @property
    def nullable_fields(self) -> list[str]:
        """Get list of nullable field names."""
        return [f.field_name for f in self.fields if f.is_nullable]

    def get_field(self, field_name: str) -> FieldMetadata | None:
        """
        Get metadata for a specific field.

        Args:
            field_name: Name of the field

        Returns:
            FieldMetadata or None if field not found
        """
        for field in self.fields:
            if field.field_name == field_name:
                return field
        return None

    def get_fields_by_type(self, field_type: str | FieldType) -> list[FieldMetadata]:
        """
        Get all fields of a specific type.

        Args:
            field_type: Type to filter by (e.g., "String", "Int", FieldType.STRING)

        Returns:
            List of fields matching the type
        """
        type_str = field_type.value if isinstance(field_type, FieldType) else field_type
        return [f for f in self.fields if f.type == type_str]

    def get_field_names(self) -> list[str]:
        """Get list of all field names."""
        return [f.field_name for f in self.fields]

    def get_field_types(self) -> dict[str, str]:
        """Get mapping of field names to their types."""
        return {f.field_name: f.type for f in self.fields}

    def has_field(self, field_name: str) -> bool:
        """Check if entity has a specific field."""
        return any(f.field_name == field_name for f in self.fields)

    def validate_fields(self, field_names: list[str]) -> tuple[list[str], list[str]]:
        """
        Validate a list of field names against this entity's schema.

        Args:
            field_names: List of field names to validate

        Returns:
            Tuple of (valid_fields, invalid_fields)
        """
        valid = []
        invalid = []
        entity_fields = set(self.get_field_names())

        for field_name in field_names:
            if field_name in entity_fields:
                valid.append(field_name)
            else:
                invalid.append(field_name)

        return valid, invalid

    def to_schema_dict(self) -> dict[str, Any]:
        """
        Convert to a schema dictionary for easy consumption.

        Returns:
            Dictionary with field schemas
        """
        return {
            "fields": [f.to_dict() for f in self.fields],
            "primary_keys": self.primary_keys,
            "required_fields": self.required_fields,
            "field_count": self.field_count,
        }
