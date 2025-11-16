# FSGW Documentation Server - Deployment Guide

## Current Deployment Status

**✅ DEPLOYED AND LIVE**

- **Public URL**: http://52.53.245.194:8100
- **Server**: ubuntu@52.53.245.194 (ip-172-32-2-80)
- **Status**: Running via PM2
- **Last Deployed**: 2025-11-16

## Access the Documentation

**Direct Access (No tunnel needed):**
Simply open in your browser: **http://52.53.245.194:8100**

The server is publicly accessible. No SSH tunnel or VPN required.

### Available Pages

- **Home**: http://52.53.245.194:8100/
- **Entity Browser**: http://52.53.245.194:8100/docs/entities
- **Entity Details**: http://52.53.245.194:8100/docs/entity/ops/auditTrail
- **API Reference**: http://52.53.245.194:8100/docs/api
- **Health Check**: http://52.53.245.194:8100/api/health
- **Swagger UI**: http://52.53.245.194:8100/docs
- **ReDoc**: http://52.53.245.194:8100/redoc

## Redeployment

To update the deployment with new code:

```bash
cd /Users/al/Projects/firstshift/fsgateway
./deployment/deploy_to_staging.sh
```

This script will:
1. ✅ Test SSH connection
2. ✅ Sync project files to the server
3. ✅ Create/update .env file with credentials
4. ✅ Install dependencies (uv, Python packages)
5. ✅ Restart the PM2 service
6. ✅ Verify the service is running

## Server Configuration

### Connection Details
- **Host**: 52.53.245.194
- **User**: ubuntu
- **SSH Key**: `.secrets/dev-planlytx.pem`
- **Port**: 22
- **Project Path**: `/home/ubuntu/fsgateway/`

### Service Configuration
- **Service Port**: 8100
- **Process Manager**: PM2
- **Service Name**: `fsgw-docs`
- **Python**: 3.13.7 (via uv)
- **Auto-restart**: Yes

### Credentials
The server uses the following FirstShift Gateway credentials (stored in `.env` on the server):

```env
FSGW_GATEWAY_URL=https://dev-cloudgateway.firstshift.ai
FSGW_TENANT_ID=7
FSGW_USERNAME=dharma.palepu+7@firstshift.ai
FSGW_PASSWORD=Plan1234
```

## Management Commands

All commands use SSH to manage the remote service.

### View Live Logs
```bash
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 logs fsgw-docs"
```

### Check Service Status
```bash
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 status"
```

### Restart Service
```bash
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 restart fsgw-docs"
```

### Stop Service
```bash
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 stop fsgw-docs"
```

### Start Service (if stopped)
```bash
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 start fsgw-docs"
```

### View Last 50 Lines of Logs
```bash
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 logs fsgw-docs --lines 50 --nostream"
```

### Check Server Health
```bash
curl http://52.53.245.194:8100/api/health
```

### Remote Shell Access
```bash
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194
cd /home/ubuntu/fsgateway
```

## PM2 Services on the VM

The server runs multiple services via PM2:

```
┌────┬───────────────────┬──────────┬────────┬─────────┬──────────┐
│ id │ name              │ mode     │ status │ restart │ uptime   │
├────┼───────────────────┼──────────┼────────┼─────────┼──────────┤
│ 2  │ backend           │ fork     │ online │ 233     │ 12D      │  ← Forecast Agent Backend
│ 26 │ frontend          │ fork     │ online │ 0       │ 12D      │  ← Forecast Agent Frontend
│ 27 │ fsgw-docs         │ fork     │ online │ 0       │ 15m      │  ← FSGW Documentation (NEW)
└────┴───────────────────┴──────────┴────────┴─────────┴──────────┘
```

**Note**: The FSGW documentation service runs independently and does not affect the forecast_agent services.

## Troubleshooting

### Service Not Responding

1. **Check if service is running:**
   ```bash
   ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 status | grep fsgw-docs"
   ```

2. **View recent errors:**
   ```bash
   ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 logs fsgw-docs --err --lines 30 --nostream"
   ```

3. **Restart the service:**
   ```bash
   ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 restart fsgw-docs"
   ```

### Connection Issues

1. **Test direct HTTP access:**
   ```bash
   curl -v http://52.53.245.194:8100/api/health
   ```

2. **Test SSH connection:**
   ```bash
   ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "echo 'SSH OK'"
   ```

3. **Check AWS security group:**
   - Ensure port 8100 is open for inbound traffic
   - Check that port 22 (SSH) is accessible

### Service Keeps Crashing

1. **Check logs for Python errors:**
   ```bash
   ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 logs fsgw-docs --lines 100"
   ```

2. **Verify .env file exists:**
   ```bash
   ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "cat /home/ubuntu/fsgateway/.env"
   ```

3. **Check Python and uv installation:**
   ```bash
   ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "which uv && uv --version"
   ```

4. **Redeploy from scratch:**
   ```bash
   ./deployment/deploy_to_staging.sh
   ```

### Update Not Reflecting

1. **Ensure deployment completed successfully:**
   ```bash
   ./deployment/deploy_to_staging.sh
   ```

2. **Hard restart PM2:**
   ```bash
   ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 delete fsgw-docs && cd /home/ubuntu/fsgateway && pm2 start bash --name fsgw-docs -- -c 'source ~/.cargo/env 2>/dev/null || true && uv run python -m fsgw.server.main --port 8100' && pm2 save"
   ```

3. **Clear browser cache** (Ctrl+Shift+R or Cmd+Shift+R)

## Security & Safety

### ✅ Safe Deployment
- Runs on separate port (8100) from forecast_agent
- Independent PM2 process
- Separate Python environment (uv)
- Can be removed without affecting forecast_agent
- Read-only documentation service

### 🔒 Security Notes
- Server is **publicly accessible** on port 8100
- AWS security group allows inbound traffic
- No authentication required (documentation is public)
- Credentials stored in `.env` on server (not in git)
- SSH key required for server management

### 🚨 Production Considerations
For production deployment, consider:
- Adding HTTPS with a domain name
- Implementing authentication/authorization
- Setting up monitoring and alerting
- Configuring log rotation
- Adding rate limiting

## Files on the Server

```
/home/ubuntu/fsgateway/
├── fsgw/                    # Python package (SDK + server)
│   ├── client/              # HTTP client & auth
│   ├── models/              # Pydantic models
│   ├── cli/                 # CLI commands
│   └── server/              # FastAPI documentation server
│       ├── main.py          # Server entry point
│       ├── templates/       # HTML templates
│       └── static/          # CSS assets
├── .venv/                   # Python virtual environment (uv)
├── .env                     # FirstShift credentials
├── pyproject.toml           # Python project config
├── uv.lock                  # Dependency lock file
└── [other files]
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS EC2 Instance                         │
│                  ip-172-32-2-80                             │
│                  52.53.245.194                              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ PM2 Process Manager                                   │  │
│  │                                                       │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────┐ │  │
│  │  │ forecast_agent │  │ forecast_agent │  │  FSGW  │ │  │
│  │  │   backend      │  │   frontend     │  │  docs  │ │  │
│  │  │   Port 5431    │  │   Port 3000    │  │  8100  │ │  │
│  │  └────────────────┘  └────────────────┘  └────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Network:                                                   │
│  - Port 22   → SSH (management)                            │
│  - Port 8100 → FSGW Documentation (public)                 │
│  - Port 5431 → Forecast Agent API (internal)               │
│  - Port 3000 → Forecast Agent UI (internal)                │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ HTTP on port 8100
                         ▼
              ┌────────────────────┐
              │   Internet Users   │
              │                    │
              │  Browser requests  │
              │  to 52.53.245.194  │
              │  on port 8100      │
              └────────────────────┘
```

## Quick Reference

| Task | Command |
|------|---------|
| **Access docs** | http://52.53.245.194:8100 |
| **Redeploy** | `./deployment/deploy_to_staging.sh` |
| **View logs** | `ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 logs fsgw-docs"` |
| **Check status** | `ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 status"` |
| **Restart service** | `ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 restart fsgw-docs"` |
| **Stop service** | `ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 stop fsgw-docs"` |
| **Health check** | `curl http://52.53.245.194:8100/api/health` |
| **SSH access** | `ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194` |

## Related Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture diagrams
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Advanced deployment options
- **[../.secrets/DEPLOYMENT_SUCCESS.md](../.secrets/DEPLOYMENT_SUCCESS.md)** - Current deployment details
- **[../.secrets/deployment_config.sh](../.secrets/deployment_config.sh)** - Server configuration

---

**Status**: ✅ **Deployed and Running**
**URL**: http://52.53.245.194:8100
**Last Updated**: 2025-11-16
