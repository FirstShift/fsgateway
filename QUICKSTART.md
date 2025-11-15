# Quick Start Guide

Get started with the FirstShift Gateway SDK in 3 minutes!

## 1. Installation

```bash
cd /Users/al/Projects/firstshift/fsgateway

# Sync dependencies
uv sync
```

## 2. Configuration

Create a `.env` file in the project root (it will be auto-loaded):

```bash
cat > .env << 'EOF'
FSGW_USERNAME=your-username
FSGW_PASSWORD=your-password
FSGW_TENANT_ID=7
FSGW_GATEWAY_URL=https://dev-cloudgateway.firstshift.ai
EOF
```

**Note**: The `.env` file is automatically loaded - no need to export variables!

## 3. Choose Your Interface

### Option A: Interactive Shell (Recommended for Exploration)

```bash
# Start interactive mode
uv run fsgw interactive

# Or if environment is activated
fsgw interactive
```

**In the interactive shell:**
```
[fsgw] > help                           # Show all commands
[fsgw] > entities                       # List all entities
[fsgw] > entities ops                   # Filter by scope
[fsgw] > info ops/auditTrail            # Get entity details
[fsgw] > search audit                   # Search entities
[fsgw] > ask "What entities are in ops scope?"  # Natural language
[fsgw] > query ops/auditTrail           # Query data
[fsgw] > metadata ops/auditTrail        # Get metadata
[fsgw] > exit                           # Exit shell
```

**Features:**
- 🎯 Tab completion for commands
- 📜 Command history (saved in `~/.fsgw_history`)
- 🎨 Rich colored output
- 💬 Natural language queries
- ⚡ Fast entity exploration

### Option B: Web Documentation Server

```bash
# Start the documentation server
uv run fsgw-server

# Or
uv run fsgw server --port 8000 --reload
```

Then visit:
- **Landing Page**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**Features:**
- 🌐 Beautiful web interface
- 📊 Browse all 239+ entities
- 🔍 Search functionality
- 📝 Field metadata viewer
- 💻 Copy-paste curl examples
- 🔄 Auto-discovery from gateway

### Option C: Command-Line Tools

```bash
# List entities
uv run fsgw entities
uv run fsgw entities --scope ops

# Get entity info
uv run fsgw info ops/auditTrail

# Search
uv run fsgw search audit

# Ask questions
uv run fsgw ask "What entities are in ops scope?"

# Query data
uv run fsgw query ops/auditTrail --limit 10
```

### Option D: Python SDK

```python
import asyncio
from fsgw import FSGWClient, QueryRequest

async def main():
    # Client auto-loads from .env
    async with FSGWClient(
        gateway_url="https://dev-cloudgateway.firstshift.ai",
        username="user",
        password="pass",
        tenant_id=7,
    ) as client:
        # List entities
        entities = await client.list_apis()
        print(f"Found {len(entities)} entities")

        # Get metadata
        metadata = await client.get_metadata("ops/auditTrail")
        print(f"Fields: {[f.field_name for f in metadata]}")

        # Query data
        query = QueryRequest().add_filter("tenantId", "=", 7).limit(10)
        results = await client.query("ops/auditTrail", query)

        for row in results:
            print(row)

asyncio.run(main())
```

## 4. Common Workflows

### Explore Available Entities

**Interactive:**
```
[fsgw] > entities
[fsgw] > entities ops
```

**CLI:**
```bash
uv run fsgw entities --scope ops
```

**Web:**
Visit http://localhost:8000/entities

### Get Entity Details

**Interactive:**
```
[fsgw] > info ops/auditTrail
```

**CLI:**
```bash
uv run fsgw info ops/auditTrail
```

**Web:**
Visit http://localhost:8000/entities/ops/auditTrail/metadata

### Query Data

**Interactive:**
```
[fsgw] > query ops/auditTrail
```

**CLI:**
```bash
uv run fsgw query ops/auditTrail --limit 10 --filter tenantId=7
```

**Python:**
```python
from fsgw import FSGWClient, QueryRequest

async with FSGWClient(...) as client:
    query = QueryRequest().add_filter("tenantId", "=", 7).limit(10)
    results = await client.query("ops/auditTrail", query)
```

### Ask Questions

**Interactive:**
```
[fsgw] > ask "What entities are in the ops scope?"
[fsgw] > ask "Show me audit trail fields"
[fsgw] > ask "How do I query data?"
```

**CLI:**
```bash
uv run fsgw ask "What entities are in ops scope?"
```

## 5. Tips & Tricks

### Interactive Mode Tips

1. **Tab Completion**: Press Tab to autocomplete commands
2. **History**: Use ↑↓ arrow keys to navigate command history
3. **Quick Info**: Type `info` without args to see usage
4. **Ctrl+C**: Won't exit - use `exit` or `quit` instead
5. **Fast Queries**: Commands run without prefix in interactive mode

### Performance Tips

1. **Use Caching**: The server caches entity and metadata responses
2. **Filter Early**: Use `--scope` to narrow results
3. **Limit Results**: Add `--limit` to query commands
4. **Interactive Mode**: Faster for multiple queries (reuses connection)

### Development Tips

1. **Auto-reload Server**: Use `--reload` flag for development
2. **Environment Variables**: Use `.env` file for credentials
3. **History File**: Clear `~/.fsgw_history` to reset command history
4. **Debug Mode**: Set `FSGW_DEBUG=true` for verbose output

## 6. Troubleshooting

### "FSGW_USERNAME and FSGW_PASSWORD must be set"

**Solution**: Create a `.env` file in the project root with your credentials.

### "Command not found: fsgw"

**Solution**: Either:
- Use `uv run fsgw` instead
- Activate the environment: `source .venv/bin/activate`

### "Connection refused"

**Solution**: Check that:
1. Your `.env` file has correct `FSGW_GATEWAY_URL`
2. You have network access to the gateway
3. Gateway is running and accessible

### Interactive mode not showing colors

**Solution**: Your terminal may not support colors. Try a modern terminal like iTerm2, Windows Terminal, or Alacritty.

## 7. Next Steps

- 📚 **Read the Docs**: [docs/README.md](docs/README.md)
- 🔍 **Explore APIs**: Start interactive mode and explore!
- 💻 **Write Code**: Use the Python SDK in your projects
- 🌐 **Browse Web UI**: Start the server and explore visually
- 📖 **Phase Docs**: Read [Phase 1](docs/phases/PHASE1_COMPLETE.md) and [Phase 2](docs/phases/PHASE2_COMPLETE.md)

## 8. Getting Help

```bash
# Show help
uv run fsgw --help

# Command-specific help
uv run fsgw entities --help
uv run fsgw query --help

# Interactive help
[fsgw] > help
```

**Support:**
- GitHub Issues: https://github.com/FirstShift/fsgateway/issues
- Documentation: [docs/README.md](docs/README.md)

---

**Happy exploring! 🚀**
