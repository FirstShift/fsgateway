# FSGW Documentation - Deployment Guide

## Quick Start

Deploy FSGW documentation to your forecast_agent VM in 3 easy steps:

### 1. Clone the Repository on VM

```bash
ssh ubuntu@your-vm-host
cd /home/ubuntu
git clone <fsgateway-repo-url> fsgateway
cd fsgateway
```

### 2. Create Environment File

```bash
cat > .env << 'EOF'
FSGW_GATEWAY_URL=https://dev-cloudgateway.firstshift.ai
FSGW_TENANT_ID=7
FSGW_USERNAME=your_username_here
FSGW_PASSWORD=your_password_here
EOF
```

### 3. Deploy with Script

**Option A: From your local machine**

```bash
export VM_HOST=your-vm-hostname
export VM_USER=ubuntu
./deploy.sh
```

**Option B: On the VM directly**

```bash
ssh ubuntu@your-vm-host
cd /home/ubuntu/fsgateway
./deploy.sh
```

That's it! The documentation will be available at `http://localhost:8100`

## What Gets Deployed

The deployment creates a new PM2 service alongside your existing forecast_agent services:

```
PM2 Services:
├── backend        (Port 5431) - forecast_agent backend
├── frontend       (Port 3000) - forecast_agent frontend
└── fsgw-docs      (Port 8100) - FSGW Documentation ← NEW
```

## Safety Guarantees

✅ **Port Isolation**: Runs on port 8100, completely separate from forecast_agent
✅ **Process Isolation**: Independent PM2 process
✅ **No Dependencies**: Separate Python environment
✅ **Quick Rollback**: `pm2 delete fsgw-docs` removes it instantly
✅ **Read-Only**: Documentation is read-only, no writes
✅ **Minimal Resources**: ~100-200 MB RAM, negligible CPU
✅ **Zero Risk**: Cannot affect forecast_agent operation

## Access the Documentation

### Locally on VM
```bash
curl http://localhost:8100
```

### Via SSH Tunnel
```bash
ssh -L 8100:localhost:8100 ubuntu@your-vm-host
# Then open: http://localhost:8100 in your browser
```

### Via Reverse Proxy
Add to nginx/caddy config for public access at `/docs/api` path.

See [DEPLOYMENT.md](DEPLOYMENT.md) for nginx/caddy configuration examples.

## Management Commands

```bash
# View real-time logs
pm2 logs fsgw-docs

# Check status
pm2 status

# Restart
pm2 restart fsgw-docs

# Stop (keeps configuration)
pm2 stop fsgw-docs

# Remove completely
pm2 delete fsgw-docs
pm2 save
```

## Update Deployment

```bash
cd /home/ubuntu/fsgateway
git pull origin main
pm2 restart fsgw-docs
```

Or run `./deploy.sh` again - it will automatically update.

## Monitoring

```bash
# Real-time monitoring
pm2 monit

# Check health
curl http://localhost:8100/api/health

# View recent logs
pm2 logs fsgw-docs --lines 50
```

## Troubleshooting

### Service won't start

```bash
# Check error logs
pm2 logs fsgw-docs --err

# Check if port is in use
sudo lsof -i :8100

# Test manually
cd /home/ubuntu/fsgateway
uv run python -m fsgw.server.main --port 8100
```

### Can't access documentation

```bash
# Check if service is running
pm2 status fsgw-docs

# Check if port is accessible
curl http://localhost:8100/api/health

# Check firewall (if accessing externally)
sudo ufw status
```

### High memory usage

```bash
# Check memory
pm2 describe fsgw-docs

# Restart to clear cache
pm2 restart fsgw-docs
```

## Documentation Structure

Once deployed, you'll have access to:

- **Home**: `http://localhost:8100/` - Overview and stats
- **Entities**: `http://localhost:8100/docs/entities` - Browse all FirstShift entities
- **Entity Details**: `http://localhost:8100/docs/entity/{scope}/{entity}` - Detailed metadata
- **API Reference**: `http://localhost:8100/docs/api` - Complete API documentation
- **JSON API**: `http://localhost:8100/api/*` - Programmatic access
- **Health Check**: `http://localhost:8100/api/health` - Service status

## Full Documentation

For detailed deployment options, automation, and configuration:

- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Quickstart**: [QUICKSTART.md](QUICKSTART.md)

## Support

If you encounter any issues:

1. Check PM2 logs: `pm2 logs fsgw-docs`
2. Verify .env file exists and has correct credentials
3. Ensure ports 5431, 3000, and 8100 are not conflicting
4. Check that uv is installed: `~/.local/bin/uv --version`

## Rollback

To completely remove the deployment:

```bash
pm2 delete fsgw-docs
pm2 save
```

This will NOT affect your forecast_agent services.
