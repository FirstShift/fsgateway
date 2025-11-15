# FSGW Documentation Deployment Guide

## Deploying to forecast_agent VM

The FSGW documentation website can be safely deployed alongside the forecast_agent on the same VM as a separate PM2 service.

### Architecture

- **forecast_agent backend**: Port 5431 (PM2: `backend`)
- **forecast_agent frontend**: Port 3000 (PM2: `frontend`)
- **FSGW docs**: Port 8100 (PM2: `fsgw-docs`) ← NEW

### Prerequisites

1. Access to the forecast_agent VM (same SSH credentials)
2. FSGW credentials (username/password for FirstShift Gateway)
3. Git access to fsgateway repository

### Deployment Steps

#### 1. Initial Setup on VM

SSH into the VM and clone the fsgateway repository:

```bash
# SSH to VM
ssh ubuntu@<VM_HOST>

# Navigate to projects directory
cd /home/ubuntu

# Clone fsgateway repository
git clone <fsgateway-repo-url> fsgateway
cd fsgateway

# Create .env file with credentials
cat > .env << 'EOF'
FSGW_GATEWAY_URL=https://dev-cloudgateway.firstshift.ai
FSGW_TENANT_ID=7
FSGW_USERNAME=your_username_here
FSGW_PASSWORD=your_password_here
EOF

# Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv sync
```

#### 2. Start with PM2

```bash
# Start FSGW docs as PM2 service
pm2 start "$HOME/.local/bin/uv run python -m fsgw.server.main --host 0.0.0.0 --port 8100" \
  --name fsgw-docs \
  --cwd /home/ubuntu/fsgateway \
  --output /home/ubuntu/fsgateway/logs/fsgw-docs.log \
  --error /home/ubuntu/fsgateway/logs/fsgw-docs-error.log

# Save PM2 configuration
pm2 save

# Verify it's running
pm2 status
pm2 logs fsgw-docs --lines 20

# Test locally
curl http://localhost:8100/api/health
```

#### 3. Configure Reverse Proxy (if using nginx/caddy)

If your VM has a reverse proxy, add a location block for FSGW docs:

**For nginx** (`/etc/nginx/sites-available/default`):

```nginx
# FSGW Documentation
location /docs/api {
    proxy_pass http://localhost:8100;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
}
```

Then reload nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

**For Caddy** (`/etc/caddy/Caddyfile`):

```caddy
# FSGW Documentation
example.com {
    handle /docs/api* {
        reverse_proxy localhost:8100
    }
}
```

Then reload Caddy:
```bash
sudo systemctl reload caddy
```

#### 4. Health Check

```bash
# Check PM2 status
pm2 status

# Check logs
pm2 logs fsgw-docs

# Test the service
curl http://localhost:8100/
curl http://localhost:8100/api/health
curl http://localhost:8100/docs/entities
```

### Management Commands

```bash
# View logs
pm2 logs fsgw-docs
pm2 logs fsgw-docs --lines 50

# Restart service
pm2 restart fsgw-docs

# Stop service
pm2 stop fsgw-docs

# Delete service (complete removal)
pm2 delete fsgw-docs
pm2 save

# Update code and restart
cd /home/ubuntu/fsgateway
git pull origin main
uv sync
pm2 restart fsgw-docs
```

### Monitoring

```bash
# Real-time monitoring
pm2 monit

# Check all services
pm2 status

# Memory usage
pm2 describe fsgw-docs
```

### Rollback

If anything goes wrong, simply remove the service:

```bash
pm2 delete fsgw-docs
pm2 save
```

This will NOT affect forecast_agent services (`backend` and `frontend`).

### Adding to GitHub Actions (Optional)

If you want to automate FSGW docs deployment, you can add it to the forecast_agent deployment workflow:

```yaml
# Add to .github/workflows/deploy.yml after frontend deployment

echo "📚 Deploying FSGW Documentation..."
if [ -d "/home/ubuntu/fsgateway" ]; then
  cd /home/ubuntu/fsgateway
  git pull origin main
  $HOME/.local/bin/uv sync

  pm2 restart fsgw-docs 2>/dev/null || \
    pm2 start "$HOME/.local/bin/uv run python -m fsgw.server.main --host 0.0.0.0 --port 8100" \
      --name fsgw-docs \
      --cwd /home/ubuntu/fsgateway \
      --output /home/ubuntu/fsgateway/logs/fsgw-docs.log \
      --error /home/ubuntu/fsgateway/logs/fsgw-docs-error.log

  echo "✅ FSGW docs deployed"

  # Health check
  if curl -fsS http://localhost:8100/api/health >/dev/null; then
    echo "✅ FSGW docs responding at http://localhost:8100"
  else
    echo "⚠️ FSGW docs health check failed" >&2
    pm2 logs fsgw-docs --lines 20
  fi
else
  echo "ℹ️ FSGW docs not deployed (directory not found)"
fi
```

### Safety Features

1. **Port Isolation**: Runs on 8100, separate from forecast_agent (5431, 3000)
2. **Process Isolation**: Independent PM2 process
3. **No Shared Dependencies**: Separate Python environment via uv
4. **Independent Logs**: Separate log files
5. **Quick Rollback**: `pm2 delete fsgw-docs` removes it completely
6. **Read-Only Service**: Docs are read-only, no write operations
7. **No Database**: Stateless service, connects only to FirstShift Gateway API

### Resource Usage

Expected resource footprint:
- **Memory**: ~100-200 MB
- **CPU**: Minimal (only active during requests)
- **Disk**: ~50 MB for code + dependencies

This is negligible compared to forecast_agent services and will NOT impact performance.

### Troubleshooting

**Service won't start:**
```bash
# Check logs
pm2 logs fsgw-docs --err

# Check if port is in use
sudo lsof -i :8100

# Verify uv is available
which uv
$HOME/.local/bin/uv --version
```

**Service crashes:**
```bash
# Check error logs
cat /home/ubuntu/fsgateway/logs/fsgw-docs-error.log

# Check environment variables
cat /home/ubuntu/fsgateway/.env

# Test manually
cd /home/ubuntu/fsgateway
uv run python -m fsgw.server.main --port 8100
```

**High memory usage:**
```bash
# Check memory
pm2 describe fsgw-docs

# Restart to clear cache
pm2 restart fsgw-docs
```

### Accessing the Documentation

Once deployed:

- **Local access**: `http://localhost:8100`
- **Public access** (with reverse proxy): `https://your-domain.com/docs/api`

### Summary

This deployment strategy is **100% safe** for your mission-critical forecast_agent because:

1. ✅ Separate PM2 process on different port
2. ✅ No shared resources or dependencies
3. ✅ Can be removed instantly without affecting forecast_agent
4. ✅ Minimal resource footprint
5. ✅ Read-only service with no side effects
6. ✅ Independent logs and monitoring
7. ✅ Optional - can be added/removed at any time

The FSGW documentation service will coexist peacefully with forecast_agent services!
