# FSGW Documentation Architecture

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Remote VM Server                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      PM2 Process Manager                   │  │
│  │                                                             │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌─────────────┐ │  │
│  │  │   backend      │  │   frontend     │  │  fsgw-docs  │ │  │
│  │  │                │  │                │  │             │ │  │
│  │  │ forecast_agent │  │ forecast_agent │  │ FSGW Docs   │ │  │
│  │  │    FastAPI     │  │    Next.js     │  │  FastAPI    │ │  │
│  │  │                │  │                │  │             │ │  │
│  │  │  Port: 5431    │  │  Port: 3000    │  │ Port: 8100  │ │  │
│  │  │                │  │                │  │             │ │  │
│  │  │ [UNTOUCHED]    │  │ [UNTOUCHED]    │  │    [NEW]    │ │  │
│  │  └────────────────┘  └────────────────┘  └─────────────┘ │  │
│  │                                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  File System:                                                    │
│  ├── /home/ubuntu/forecast_agent/    [Existing - Untouched]    │
│  │   ├── vibescm/                                               │
│  │   ├── ux/web/                                                │
│  │   └── logs/                                                  │
│  │                                                               │
│  └── /home/ubuntu/fsgateway/         [New - FSGW Docs]         │
│      ├── fsgw/                                                   │
│      ├── .env                                                    │
│      └── logs/                                                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ SSH Connection
                            │ (Port 22 or custom)
                            │
┌───────────────────────────┼──────────────────────────────────────┐
│                    Your Local Machine                            │
│                                                                   │
│  Terminal Commands:                                              │
│  ├── ./setup_deployment.sh     [Setup & test connection]       │
│  ├── ./deploy_remote.sh        [Deploy to VM]                  │
│  └── ssh -L 8100:localhost:8100 [Access via tunnel]            │
│                                                                   │
│  Browser:                                                        │
│  └── http://localhost:8100     [Access FSGW docs]              │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Network Flow

```
User (Browser)
    │
    │ HTTP Request to localhost:8100
    │
    ▼
SSH Tunnel
(Local Port 8100 → Remote Port 8100)
    │
    │ Encrypted SSH Connection
    │
    ▼
Remote VM: localhost:8100
    │
    │ FastAPI Server
    │
    ▼
┌─────────────────────────────────────────────┐
│          FSGW Documentation Service         │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │   Jinja2 Templates (HTML)              │ │
│  │   ├── Home Page                        │ │
│  │   ├── Entities Browser                 │ │
│  │   ├── Entity Details                   │ │
│  │   └── API Reference                    │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │   JSON API Endpoints                   │ │
│  │   ├── /api/health                      │ │
│  │   ├── /api/entities                    │ │
│  │   ├── /api/search                      │ │
│  │   └── /api/entities/{scope}/{entity}   │ │
│  └────────────────────────────────────────┘ │
│                                              │
└──────────────┬───────────────────────────────┘
               │
               │ HTTPS API Calls
               │
               ▼
┌─────────────────────────────────────────────┐
│    FirstShift Gateway API                   │
│    https://dev-cloudgateway.firstshift.ai   │
│                                              │
│    Returns entity metadata and data         │
└─────────────────────────────────────────────┘
```

## Component Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                  FSGW Documentation Service                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    Web Layer (FastAPI)                    │ │
│  │                                                            │ │
│  │  HTML Routes:              JSON API Routes:               │ │
│  │  ├── GET /                 ├── GET /api/health           │ │
│  │  ├── GET /docs/entities    ├── GET /api/entities         │ │
│  │  ├── GET /docs/entity/...  ├── GET /api/entities/{scope} │ │
│  │  └── GET /docs/api         └── GET /api/search           │ │
│  │                                                            │ │
│  └──────────────────┬─────────────────────────────────────────┘ │
│                     │                                            │
│  ┌──────────────────▼─────────────────────────────────────────┐ │
│  │             Template Engine (Jinja2)                       │ │
│  │                                                             │ │
│  │  Templates:                Static Assets:                  │ │
│  │  ├── base.html             ├── CSS (modern styling)       │ │
│  │  ├── index.html            └── JS (search, filtering)     │ │
│  │  ├── entities.html                                         │ │
│  │  ├── entity_detail.html                                    │ │
│  │  └── api_reference.html                                    │ │
│  │                                                             │ │
│  └──────────────────┬──────────────────────────────────────────┘ │
│                     │                                            │
│  ┌──────────────────▼─────────────────────────────────────────┐ │
│  │              Client Layer (FSGW Client)                    │ │
│  │                                                             │ │
│  │  ├── FSGWClient (httpx async)                             │ │
│  │  ├── AuthClient (token management)                        │ │
│  │  ├── Caching (entities, metadata)                         │ │
│  │  └── Models (Pydantic v2)                                 │ │
│  │                                                             │ │
│  └──────────────────┬──────────────────────────────────────────┘ │
│                     │                                            │
└─────────────────────┼────────────────────────────────────────────┘
                      │
                      │ HTTPS (access-token header)
                      │
                      ▼
            FirstShift Gateway API
```

## Data Flow

### User Browses Entities

```
1. User → Browser: http://localhost:8100/docs/entities
                         ↓
2. SSH Tunnel → Remote VM: Port 8100
                         ↓
3. FastAPI → docs_entities_page()
                         ↓
4. FSGWClient → discover_entities()
                         ↓
5. FirstShift API → GET /api/v1/metadata/endpoints
                         ↓
6. Response ← JSON with all entities
                         ↓
7. Jinja2 ← entities.html template
                         ↓
8. HTML ← Rendered page with searchable table
                         ↓
9. Browser ← Display entities
```

### User Views Entity Details

```
1. User → Click on entity (e.g., "auditTrail")
                         ↓
2. Browser → http://localhost:8100/docs/entity/ops/auditTrail
                         ↓
3. FastAPI → docs_entity_page(scope="ops", entity="auditTrail")
                         ↓
4. FSGWClient → get_api_info() + get_metadata()
                         ↓
5. FirstShift API → GET /api/v1/ops/auditTrail/info
                    GET /api/v1/ops/auditTrail/fields
                         ↓
6. Jinja2 ← entity_detail.html template
                         ↓
7. HTML ← Rendered page with:
           - Field metadata table
           - Primary keys highlighted
           - Query examples (Python, REST, CLI)
                         ↓
8. Browser ← Display detailed entity info
```

## Security Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Security Layers                            │
│                                                                  │
│  1. SSH Authentication                                          │
│     ├── Private key authentication (not password)              │
│     ├── Key permissions enforced (600)                         │
│     └── Encrypted tunnel for all traffic                       │
│                                                                  │
│  2. Environment Isolation                                       │
│     ├── .env file (not in git)                                │
│     ├── Credentials stored locally on VM                       │
│     └── No credentials in code/templates                       │
│                                                                  │
│  3. Network Isolation                                           │
│     ├── Service runs on localhost only (127.0.0.1)            │
│     ├── Access only via SSH tunnel                            │
│     └── No direct external exposure                            │
│                                                                  │
│  4. Process Isolation                                           │
│     ├── Separate PM2 process                                   │
│     ├── Separate Python environment (uv)                       │
│     ├── Separate port (8100)                                   │
│     └── Independent logs                                        │
│                                                                  │
│  5. API Security                                                │
│     ├── Access token authentication to FirstShift              │
│     ├── Token auto-refresh                                     │
│     └── HTTPS to external API                                  │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## Resource Usage

```
┌────────────────────────────────────────────────────────────────┐
│                    Expected Resource Footprint                  │
│                                                                  │
│  Memory:    ~100-200 MB (minimal)                              │
│  CPU:       < 1% idle, 2-5% during requests                    │
│  Disk:      ~50 MB (code + dependencies)                       │
│  Network:   Minimal (only API calls to FirstShift)            │
│                                                                  │
│  Impact on forecast_agent: ZERO                                │
│  (Separate process, port, environment)                         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## Deployment Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Deployment Steps                             │
│                                                                   │
│  Local Machine:                                                  │
│  1. ./setup_deployment.sh    → Test connection, save config    │
│                                                                   │
│  2. ./deploy_remote.sh       → Trigger deployment               │
│                                  │                                │
│                                  ▼                                │
│  Remote VM:                                                      │
│  3. rsync files              → Copy code to /home/ubuntu/fsgw...│
│                                                                   │
│  4. Copy .env                → Transfer credentials             │
│                                                                   │
│  5. uv sync                  → Install Python dependencies      │
│                                                                   │
│  6. PM2 start/restart        → Launch service on port 8100      │
│                                                                   │
│  7. Health check             → Verify /api/health responds      │
│                                                                   │
│  8. PM2 save                 → Persist configuration            │
│                                  │                                │
│                                  ▼                                │
│  Local Machine:                                                  │
│  9. SSH tunnel               → Access via localhost:8100        │
│                                                                   │
│  10. Browser                 → View documentation               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. **Server-Side Rendering**
- Dynamic content generated on-demand
- No client-side framework needed
- Fast page loads

### 2. **Entity Discovery**
- Auto-discovers 239+ entities from FirstShift API
- Grouped by scope (ops, data, config, metadata, rbac, globalmeta)
- Cached for performance

### 3. **Searchable Interface**
- Real-time JavaScript search
- Filter by scope
- Sort by name/description

### 4. **Detailed Metadata**
- Complete field information
- Primary keys highlighted
- Data types and constraints
- Nullable indicators

### 5. **Code Examples**
- Python SDK examples
- REST API with curl
- CLI commands
- Copy-paste ready

### 6. **Dual Interface**
- HTML documentation for humans
- JSON API for programmatic access
- Both accessible from same service
