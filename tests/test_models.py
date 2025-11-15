"""Tests for data models."""

from fsgw.models import (
    EndpointEntity,
    EndpointGroup,
    EndpointsResponse,
    FieldConstraint,
    FieldMetadata,
    MetadataResponse,
    QueryRequest,
    QueryResponse,
)


def test_endpoint_entity_creation():
    """Test EndpointEntity model."""
    entity = EndpointEntity(
        name="products",
        display_name="Products",
        description="Product catalog",
        endpoint="/api/v1/query/products",
        methods=["GET", "POST"],
    )

    assert entity.name == "products"
    assert entity.display_name == "Products"
    assert "GET" in entity.methods


def test_endpoint_group_creation():
    """Test EndpointGroup model."""
    entity = EndpointEntity(
        name="products",
        endpoint="/api/v1/query/products",
        methods=["GET"],
    )

    group = EndpointGroup(
        name="catalog",
        display_name="Catalog",
        entities=[entity],
    )

    assert group.name == "catalog"
    assert len(group.entities) == 1
    assert group.entities[0].name == "products"


def test_field_metadata_creation():
    """Test FieldMetadata model."""
    constraint = FieldConstraint(
        type="length",
        value={"min": 1, "max": 100},
    )

    field = FieldMetadata(
        name="product_id",
        display_name="Product ID",
        data_type="string",
        required=True,
        nullable=False,
        is_primary_key=True,
        constraints=[constraint],
    )

    assert field.name == "product_id"
    assert field.is_primary_key is True
    assert len(field.constraints) == 1


def test_query_request_defaults():
    """Test QueryRequest with defaults."""
    request = QueryRequest()

    assert request.filters is None
    assert request.sort_order == "asc"
    assert request.page == 1
    assert request.limit == 100


def test_query_request_with_filters():
    """Test QueryRequest with filters."""
    request = QueryRequest(
        filters={"category": "electronics", "price": {"$gt": 100}},
        sort_by="price",
        sort_order="desc",
        page=2,
        limit=50,
    )

    assert request.filters == {"category": "electronics", "price": {"$gt": 100}}
    assert request.sort_by == "price"
    assert request.sort_order == "desc"
    assert request.page == 2
    assert request.limit == 50


def test_query_response_creation():
    """Test QueryResponse model."""
    response = QueryResponse(
        entity="products",
        items=[
            {"id": "1", "name": "Product 1"},
            {"id": "2", "name": "Product 2"},
        ],
        total=100,
        page=1,
        limit=50,
        total_pages=2,
        has_next=True,
        has_prev=False,
    )

    assert response.entity == "products"
    assert len(response.items) == 2
    assert response.total == 100
    assert response.has_next is True
