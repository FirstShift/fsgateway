# SDK Development Checklist

## Phase 1: Core Models ✅ COMPLETE

### 1.1 Authentication Models
- [x] Update `fsgw/auth/models.py` with complete auth models
  - [x] AuthInput (username, password, tenantId)
  - [x] AuthOutput (access-token, refresh-token with aliases)
  - [x] Token validation and expiry checking

### 1.2 API Response Models
- [x] Create `fsgw/models/responses.py`
  - [x] BaseResponse (status, statusCode, message)
  - [x] DataResponse[T] (generic with data field)
  - [x] Comprehensive error handling

### 1.3 Entity Models
- [x] Update `fsgw/models/endpoints.py`
  - [x] EndpointEntity (apiScope, apiUrl, externalAPIName, description)
  - [x] EndpointsResponse with entities field
  - [x] Type-safe model with Pydantic v2

### 1.4 Metadata Models
- [x] Update `fsgw/models/metadata.py`
  - [x] FieldMetadata (fieldName, type, isPrimaryKey, etc.)
  - [x] MetadataResponse with validation
  - [x] Complete field metadata handling

### 1.5 Query Models
- [x] Update `fsgw/models/query.py`
  - [x] FilterCriteria (key, operation, value, prefixOperation)
  - [x] SortOrder (column, sortOrder)
  - [x] QueryRequest (criteriaList, orderByList, selectFieldsList, offset, limit)
  - [x] Fluent builder methods (.add_filter(), .order_by(), .limit(), etc.)
  - [x] QueryResponse with full result handling

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

## Phase 3: API Methods ✅ COMPLETE

### 3.1 API #1 - Discovery
- [x] Add to FSGWClient:
  - [x] `async def list_apis() -> list[EndpointEntity]`
  - [x] `async def list_apis_by_scope(scope: str) -> list[EndpointEntity]`
  - [x] `async def get_api_info(api_url: str) -> EndpointEntity`
  - [x] Cache discovery results for performance (in-memory caching)

### 3.2 API #2 - Metadata
- [x] Add to FSGWClient:
  - [x] `async def get_metadata(api_url: str) -> list[FieldMetadata]`
  - [x] Metadata retrieval with full field details

### 3.3 API #3 - Query
- [x] Add to FSGWClient:
  - [x] `async def query(api_url: str, request: QueryRequest) -> QueryResponse`
  - [x] Full QueryRequest support with filters, sorting, pagination
  - [x] QueryResponse with records and row count

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

## Phase 6: Error Handling ✅ COMPLETE

### 6.1 Custom Exceptions
- [x] Create `fsgw/exceptions.py`
  - [x] FSGWException (base)
  - [x] AuthenticationError
  - [x] AuthorizationError
  - [x] APIError
  - [x] ValidationError
  - [x] NetworkError
  - [x] TimeoutError
  - [x] 11 total exception types

### 6.2 Error Response Parsing
- [x] Parse API error responses
- [x] Convert HTTP status codes to exceptions
- [x] Include detailed error context with status codes and URLs

---

## Phase 3.5: CLI & Documentation Website ✅ COMPLETE (Bonus)

### 3.5.1 Interactive CLI
- [x] Create `fsgw/cli/main.py`
  - [x] Typer-based CLI with multiple commands
  - [x] Interactive REPL mode with prompt_toolkit
  - [x] Command history and tab completion
  - [x] Auto-load .env configuration
  - [x] Rich terminal output with colored tables
  - [x] Commands: entities, search, info, metadata, query, ask, interactive

### 3.5.2 Documentation Website
- [x] Create `fsgw/server/main.py`
  - [x] FastAPI server with Jinja2 templates
  - [x] Server-side rendered HTML documentation
  - [x] Beautiful, responsive UI with modern CSS
  - [x] Searchable entity browser (239+ entities)
  - [x] Detailed entity pages with field metadata
  - [x] API reference documentation
  - [x] Code examples (Python SDK, REST API, CLI)
  - [x] JSON API endpoints for programmatic access
  - [x] Scope-specific color coding

### 3.5.3 Templates & Assets
- [x] Create `fsgw/server/templates/`
  - [x] base.html - Base layout with header/nav
  - [x] index.html - Home page with stats and overview
  - [x] entities.html - Searchable entity browser
  - [x] entity_detail.html - Detailed entity page
  - [x] api_reference.html - API documentation
- [x] Create `fsgw/server/static/css/style.css`
  - [x] Modern, clean design
  - [x] Responsive layout
  - [x] Scope-specific colors
  - [x] Proper typography and spacing

### 3.5.4 Deployment Infrastructure
- [x] Create `deployment/` directory
  - [x] setup_deployment.sh - Interactive setup
  - [x] deploy.sh - Manual deployment script
  - [x] SETUP_GUIDE.md - Step-by-step guide
  - [x] ARCHITECTURE.md - System diagrams
  - [x] DEPLOYMENT.md - Advanced options
  - [x] .secrets/ directory for credentials (gitignored)

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

### Completed Phases
- [x] **Phase 1**: Core Models ✅ COMPLETE
  - All Pydantic models with proper type hints
  - QueryRequest with fluent builder methods
  - Authentication, endpoints, metadata, query models

- [x] **Phase 2**: Client Infrastructure ✅ COMPLETE
  - BaseClient with httpx, retries, connection pooling
  - AuthClient with token caching and auto-refresh
  - FSGWClient with context manager support
  - 11 custom exception types
  - Comprehensive error handling

- [x] **Phase 3**: API Methods ✅ COMPLETE
  - All three FirstShift APIs implemented
  - Discovery: list_apis(), list_apis_by_scope(), get_api_info()
  - Metadata: get_metadata()
  - Query: query() with full QueryRequest support
  - Entity caching for performance

- [x] **Phase 6**: Error Handling ✅ COMPLETE
  - Custom exception hierarchy
  - HTTP status code mapping
  - Detailed error context

- [x] **Phase 3.5**: CLI & Documentation Website ✅ COMPLETE (Bonus)
  - Interactive CLI with REPL mode
  - Beautiful documentation website (FastAPI + Jinja2)
  - 239+ entities browser with search
  - Deployment infrastructure

### Code Statistics
- **Total Lines**: ~3,500+ lines
- **Main Package**: fsgw/ (client, models, auth, cli, server)
- **Templates**: 5 HTML templates
- **CSS**: Modern responsive design
- **Tests**: Integration tests in tests/integration/

### What Works Now
1. **Python SDK**: Fully functional async client
   ```python
   async with FSGWClient(...) as client:
       entities = await client.list_apis()
       metadata = await client.get_metadata("ops/auditTrail")
       results = await client.query("ops/auditTrail", QueryRequest().limit(10))
   ```

2. **CLI**: Interactive commands
   ```bash
   uv run fsgw interactive    # REPL mode
   uv run fsgw entities       # List all entities
   uv run fsgw search "audit" # Search entities
   uv run fsgw query ops/auditTrail  # Query data
   ```

3. **Documentation Server**: Local web docs
   ```bash
   uv run fsgw server  # http://localhost:8000
   ```

### Remaining Work (Optional Enhancements)

**Phase 4**: Decorator Pattern (shiftfm-style)
- [ ] @fsgw_client decorator for auto-injection
- [ ] Entity-specific decorators

**Phase 5**: Query Builder
- [ ] Fluent QueryBuilder class (more advanced than current)
- [ ] .execute() method

**Phase 7**: Documentation
- [ ] Complete type hints coverage (partially done)
- [ ] Comprehensive docstrings
- [ ] Sphinx/MkDocs API docs

**Phase 8**: Testing
- [ ] Unit tests for all modules
- [ ] Mock tests for offline testing
- [ ] >80% code coverage

**Phase 9**: Optimization
- [ ] Metadata caching with TTL
- [ ] Batch query support
- [ ] Stream large result sets

**Phase 10**: Examples
- [ ] Basic usage examples
- [ ] Supply chain specific examples

**Phase 11**: Package & Distribution
- [ ] Package metadata cleanup
- [ ] CI/CD with GitHub Actions
- [ ] PyPI distribution

### Next Steps

**Option 1: Production Ready** (Recommended)
1. Add comprehensive unit tests (Phase 8)
2. Complete docstrings (Phase 7.2)
3. Add more examples (Phase 10)
4. Setup CI/CD (Phase 11)

**Option 2: Enhanced Features**
1. Implement decorator pattern (Phase 4)
2. Build advanced QueryBuilder (Phase 5)
3. Add caching improvements (Phase 9)

**Option 3: Polish & Deploy**
1. Deploy documentation website to production
2. Create video tutorials
3. Write comprehensive user guide

**Current State**: SDK is **functional and usable** for all core operations. The remaining phases are enhancements, polish, and production-readiness improvements.
