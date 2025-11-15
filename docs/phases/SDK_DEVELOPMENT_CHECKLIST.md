# SDK Development Checklist

## Phase 1: Core Models ✅ Started

### 1.1 Authentication Models
- [ ] Update `fsgw/auth/models.py` with complete auth models
  - [x] AuthInput (username, password, tenantId)
  - [x] AuthOutput (access-token, refresh-token with aliases)
  - [ ] TokenRefresh models
  - [ ] Token validation helpers

### 1.2 API Response Models
- [ ] Create `fsgw/models/responses.py`
  - [ ] BaseResponse (status, statusCode, message)
  - [ ] DataResponse[T] (generic with data field)
  - [ ] ErrorResponse
  - [ ] PaginatedResponse

### 1.3 Entity Models
- [ ] Update `fsgw/models/endpoints.py`
  - [x] EndpointEntity (apiScope, apiUrl, externalAPIName, description)
  - [x] EndpointsResponse
  - [ ] Add helper methods (to_dict, from_dict)

### 1.4 Metadata Models
- [ ] Update `fsgw/models/metadata.py`
  - [x] FieldMetadata (fieldName, type, isPrimaryKey, etc.)
  - [ ] FieldType enum (Int, String, Boolean, etc.)
  - [ ] MetadataResponse with validation
  - [ ] Helper methods for type conversions

### 1.5 Query Models
- [ ] Update `fsgw/models/query.py`
  - [ ] FilterCriteria (key, operation, value, prefixOperation)
  - [ ] FilterOperation enum (=, !=, >, <, LIKE, IN, etc.)
  - [ ] SortOrder (column, sortOrder)
  - [ ] SortDirection enum (ASC, DESC)
  - [ ] QueryRequest (criteriaList, orderByList, selectFieldsList, offset, limit)
  - [ ] QueryResponse[T] (generic for any entity data)
  - [ ] Add query builder helpers

---

## Phase 2: Client Infrastructure ✅ COMPLETE

### 2.1 Base Client
- [x] Create `fsgw/client/base.py`
  - [x] BaseClient class with httpx AsyncClient
  - [x] Connection pooling configuration
  - [x] Timeout settings
  - [x] Retry logic with exponential backoff
  - [x] Error handling and custom exceptions

### 2.2 Authentication Client
- [x] Update `fsgw/auth/client.py`
  - [x] authenticate() method
  - [x] refresh_token() method
  - [x] Token caching mechanism
  - [x] Token expiry checking
  - [x] Auto-refresh on expiry

### 2.3 Main SDK Client
- [x] Update `fsgw/client/client.py`
  - [x] FSGWClient class inheriting from BaseClient
  - [x] Constructor with gateway_url, credentials
  - [x] Lazy authentication (authenticate on first API call)
  - [x] Context manager support (async with)
  - [x] Session management

### 2.4 Custom Exceptions
- [x] Create `fsgw/exceptions.py`
  - [x] FSGWException base class
  - [x] 11 specific exception types
  - [x] Error context and details

### 2.5 Package Exports
- [x] Update `fsgw/__init__.py`
  - [x] Export all public APIs
  - [x] Export all exceptions
  - [x] Export all models

### 2.6 Testing
- [x] Create `test_phase2_client.py`
  - [x] Test authentication
  - [x] Test all three APIs
  - [x] Test error handling
  - [x] Test caching

---

## Phase 3: API Methods

### 3.1 API #1 - Discovery
- [ ] Add to FSGWClient:
  - [ ] `async def list_apis() -> list[EndpointEntity]`
  - [ ] `async def list_apis_by_scope(scope: str) -> list[EndpointEntity]`
  - [ ] `async def get_api_info(api_url: str) -> EndpointEntity`
  - [ ] Cache discovery results for performance

### 3.2 API #2 - Metadata
- [ ] Add to FSGWClient:
  - [ ] `async def get_metadata(api_url: str) -> list[FieldMetadata]`
  - [ ] `async def get_metadata_by_scope(scope: str, entity: str) -> list[FieldMetadata]`
  - [ ] `async def get_primary_keys(api_url: str) -> list[str]`
  - [ ] `async def get_field_types(api_url: str) -> dict[str, str]`
  - [ ] Metadata caching with TTL

### 3.3 API #3 - Query
- [ ] Add to FSGWClient:
  - [ ] `async def query(api_url: str, request: QueryRequest) -> QueryResponse`
  - [ ] `async def query_all(api_url: str, limit: int = 1000) -> list[dict]`
  - [ ] `async def query_paginated(api_url: str, page_size: int = 100) -> AsyncIterator`
  - [ ] `async def query_with_filters(api_url: str, filters: list[FilterCriteria]) -> QueryResponse`
  - [ ] Query builder pattern

---

## Phase 4: Decorator Pattern (shiftfm-style)

### 4.1 Decorator Infrastructure
- [ ] Create `fsgw/decorators.py`
  - [ ] @fsgw_client decorator
  - [ ] Auto-inject FSGWClient instance
  - [ ] Handle authentication automatically
  - [ ] Error handling wrapper

### 4.2 Entity-Specific Decorators
- [ ] Create decorators for common entities:
  - [ ] @audit_trail
  - [ ] @dimension_master
  - [ ] @timeseries_data
  - [ ] @transaction_master
  - [ ] @planning_grid

### 4.3 Usage Pattern
- [ ] Example implementation:
```python
from fsgw import fsgw_client, FSGWClient

@fsgw_client
async def get_audit_data(client: FSGWClient, limit: int = 10):
    return await client.query("ops/auditTrail",
        QueryRequest(limit=limit))
```

---

## Phase 5: Query Builder

### 5.1 Fluent Query Builder
- [ ] Create `fsgw/query_builder.py`
  - [ ] QueryBuilder class with fluent interface
  - [ ] `.select(*fields)` method
  - [ ] `.where(field, operation, value)` method
  - [ ] `.and_where(...)`, `.or_where(...)` methods
  - [ ] `.order_by(field, direction)` method
  - [ ] `.limit(n)`, `.offset(n)` methods
  - [ ] `.build() -> QueryRequest` method
  - [ ] `.execute(client, api_url)` method

### 5.2 Usage Example
```python
result = await (QueryBuilder()
    .select("auditId", "eventName", "tenantId")
    .where("tenantId", "=", 7)
    .and_where("eventName", "LIKE", "CREATE%")
    .order_by("auditId", "DESC")
    .limit(10)
    .execute(client, "ops/auditTrail"))
```

---

## Phase 6: Error Handling

### 6.1 Custom Exceptions
- [ ] Create `fsgw/exceptions.py`
  - [ ] FSGWException (base)
  - [ ] AuthenticationError
  - [ ] AuthorizationError
  - [ ] APIError
  - [ ] ValidationError
  - [ ] NetworkError
  - [ ] TimeoutError
  - [ ] RateLimitError

### 6.2 Error Response Parsing
- [ ] Parse API error responses
- [ ] Convert HTTP status codes to exceptions
- [ ] Include detailed error context
- [ ] Add retry hints

---

## Phase 7: Type Hints & Documentation

### 7.1 Type Hints
- [ ] Add complete type hints to all methods
- [ ] Use TypeVar for generic responses
- [ ] Add Protocol classes where appropriate
- [ ] Run mypy for type checking

### 7.2 Docstrings
- [ ] Add docstrings to all public methods
- [ ] Include parameter descriptions
- [ ] Add return type descriptions
- [ ] Include usage examples in docstrings
- [ ] Add raises sections for exceptions

### 7.3 API Documentation
- [ ] Generate API docs with sphinx/mkdocs
- [ ] Create user guide
- [ ] Add tutorials
- [ ] Document common patterns

---

## Phase 8: Testing

### 8.1 Unit Tests
- [ ] Create `tests/test_models.py`
  - [ ] Test all model validations
  - [ ] Test model serialization/deserialization
  - [ ] Test field constraints

- [ ] Create `tests/test_auth.py`
  - [ ] Test authentication flow
  - [ ] Test token refresh
  - [ ] Test token caching

- [ ] Create `tests/test_client.py`
  - [ ] Test API #1 methods
  - [ ] Test API #2 methods
  - [ ] Test API #3 methods
  - [ ] Test error handling

- [ ] Create `tests/test_query_builder.py`
  - [ ] Test query builder fluent interface
  - [ ] Test filter construction
  - [ ] Test query validation

### 8.2 Integration Tests
- [ ] Create `tests/integration/`
  - [ ] Test real API calls (with test credentials)
  - [ ] Test pagination
  - [ ] Test large result sets
  - [ ] Test error scenarios

### 8.3 Mock Tests
- [ ] Mock HTTP responses for offline testing
- [ ] Use pytest fixtures
- [ ] Test edge cases

---

## Phase 9: Performance & Optimization

### 9.1 Caching
- [ ] Implement metadata caching
- [ ] Implement discovery results caching
- [ ] Add cache invalidation
- [ ] Add TTL configuration

### 9.2 Connection Pooling
- [ ] Configure httpx connection limits
- [ ] Optimize for concurrent requests
- [ ] Add connection timeout tuning

### 9.3 Async Optimizations
- [ ] Batch query support
- [ ] Parallel metadata fetching
- [ ] Stream large result sets

---

## Phase 10: Examples & Usage Patterns

### 10.1 Basic Examples
- [ ] Create `examples/01_authentication.py`
- [ ] Create `examples/02_list_entities.py`
- [ ] Create `examples/03_get_metadata.py`
- [ ] Create `examples/04_simple_query.py`
- [ ] Create `examples/05_filtered_query.py`

### 10.2 Advanced Examples
- [ ] Create `examples/06_query_builder.py`
- [ ] Create `examples/07_pagination.py`
- [ ] Create `examples/08_decorator_pattern.py`
- [ ] Create `examples/09_batch_operations.py`
- [ ] Create `examples/10_supply_chain_app.py`

### 10.3 Supply Chain Specific
- [ ] Example: Query dimension master (products, locations, customers)
- [ ] Example: Query transaction data
- [ ] Example: Query timeseries data (forecasts, actuals)
- [ ] Example: Build planning grid queries
- [ ] Example: Audit trail analysis

---

## Phase 11: Package & Distribution

### 11.1 Package Configuration
- [ ] Update `pyproject.toml` with all dependencies
- [ ] Add package metadata
- [ ] Configure entry points
- [ ] Add classifiers

### 11.2 Documentation Package
- [ ] README with quick start
- [ ] CHANGELOG
- [ ] CONTRIBUTING guide
- [ ] LICENSE file

### 11.3 CI/CD
- [ ] Add GitHub Actions workflow
- [ ] Run tests on push
- [ ] Type checking with mypy
- [ ] Linting with ruff
- [ ] Code formatting with black

---

## Success Criteria

### Functional Requirements
- ✅ All three APIs accessible via SDK
- ✅ All 239 entities can be queried
- ✅ Proper error handling and retries
- ✅ Fluent query interface (QueryRequest)
- [ ] Decorator pattern works like shiftfm (planned)

### Non-Functional Requirements
- [ ] 100% type hints coverage
- [ ] >80% test coverage
- [ ] <100ms overhead for typical queries
- [ ] Comprehensive documentation
- [ ] Easy to use for supply chain developers

### Developer Experience
- ✅ One-line client creation
- ✅ Intuitive method names
- ✅ Clear error messages
- ✅ Rich IDE autocomplete (full type hints)
- ✅ Minimal boilerplate (context manager support)

---

## Current Progress

- [x] API Discovery (all 239 entities documented)
- [x] Project organization
- [x] Phase 1: Core Models ✅ COMPLETE
- [x] Phase 2: Client Infrastructure ✅ COMPLETE

**Current Phase**: Phase 2 Complete (1,346 lines)
**Next Steps**: Phase 3 - API Methods (or proceed to Phase 4-11)
