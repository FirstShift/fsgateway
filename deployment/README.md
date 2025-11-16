# FSGW Documentation Deployment

This directory contains scripts and documentation for deploying the FSGW documentation server to a remote VM.

## 🎉 Current Status

**✅ DEPLOYED AND LIVE**

**Public URL**: http://52.53.245.194:8100

The documentation website is running on the staging server and is publicly accessible.

## Quick Links

| Document | Purpose |
|----------|---------|
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Complete deployment guide with all commands |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System architecture and diagrams |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Advanced deployment options |
| **[deploy_to_staging.sh](deploy_to_staging.sh)** | Automated deployment script |

## Quick Start

### Access the Documentation
Simply open in your browser:
**http://52.53.245.194:8100**

No SSH tunnel or VPN required.

### Redeploy/Update
```bash
./deployment/deploy_to_staging.sh
```

### View Logs
```bash
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 logs fsgw-docs"
```

### Check Status
```bash
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 status"
```

## Server Details

- **Host**: 52.53.245.194
- **User**: ubuntu
- **SSH Key**: `.secrets/dev-planlytx.pem`
- **Project Path**: `/home/ubuntu/fsgateway/`
- **Service Port**: 8100
- **Process Manager**: PM2
- **Service Name**: `fsgw-docs`

## Files in This Directory

```
deployment/
├── README.md                  # This file
├── SETUP_GUIDE.md            # Complete deployment guide
├── ARCHITECTURE.md           # System architecture
├── DEPLOYMENT.md             # Advanced deployment options
├── deploy_to_staging.sh      # Automated deployment script
├── deploy.sh                 # Legacy deployment script
└── setup_deployment.sh       # Legacy setup script
```

## Deployment Architecture

```
Local Machine                      Remote Server (52.53.245.194)
─────────────                      ──────────────────────────────

fsgateway/                         /home/ubuntu/fsgateway/
├── fsgw/                   ───▶   ├── fsgw/
├── .env.example                   ├── .env (created from config)
├── deployment/                    ├── .venv/ (uv managed)
│   └── deploy_to_staging.sh      └── [all project files]
└── .secrets/
    ├── dev-planlytx.pem                    │
    └── deployment_config.sh                │
                                            ▼
         rsync via SSH              PM2 Process Manager
                                            │
                                            ▼
                                    fsgw-docs service
                                    (Port 8100)
                                            │
                                            ▼
                              Public HTTP Access
                              http://52.53.245.194:8100
```

## Common Tasks

### Management
```bash
# View live logs
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 logs fsgw-docs"

# Restart service
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 restart fsgw-docs"

# Stop service
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 stop fsgw-docs"

# Check all PM2 services
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 status"
```

### Testing
```bash
# Test HTTP access
curl http://52.53.245.194:8100/api/health

# Test SSH connection
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "echo 'SSH OK'"
```

### Updates
```bash
# Full redeploy (recommended)
./deployment/deploy_to_staging.sh

# Quick restart (after manual file changes)
ssh -i .secrets/dev-planlytx.pem ubuntu@52.53.245.194 "pm2 restart fsgw-docs"
```

## Troubleshooting

If you encounter issues:

1. **Check [SETUP_GUIDE.md](SETUP_GUIDE.md)** - Contains detailed troubleshooting section
2. **View service logs** - `ssh ... "pm2 logs fsgw-docs"`
3. **Verify service status** - `ssh ... "pm2 status"`
4. **Test connectivity** - `curl http://52.53.245.194:8100/api/health`
5. **Redeploy** - `./deployment/deploy_to_staging.sh`

## Security

- Server is **publicly accessible** on port 8100
- SSH key required for server management
- Credentials stored in `.env` on server (not in git)
- Independent service that doesn't affect forecast_agent

## Documentation

For complete documentation, see:
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Step-by-step guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture details
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Advanced options

---

**Status**: ✅ **Live and Running**
**URL**: http://52.53.245.194:8100
**Last Updated**: 2025-11-16
