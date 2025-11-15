# FSGW Documentation Deployment

This directory contains all deployment-related files and documentation for deploying the FSGW documentation website to your remote VM.

## Files

| File | Description |
|------|-------------|
| **setup_deployment.sh** | Interactive setup script - test connection & save config |
| **deploy.sh** | Manual deployment script (for on-VM deployment) |
| **SETUP_GUIDE.md** | Complete step-by-step deployment guide |
| **ARCHITECTURE.md** | System architecture and diagrams |
| **DEPLOYMENT.md** | Advanced deployment options |
| **README_DEPLOYMENT.md** | Quick reference guide |

## Quick Start

### Option 1: Automated Setup (Recommended)

Run the interactive setup script:

```bash
cd /Users/al/Projects/firstshift/fsgateway
./deployment/setup_deployment.sh
```

This will:
1. Prompt for your VM connection details (IP, username, SSH key path)
2. Test the SSH connection
3. Check the VM environment
4. Save configuration securely
5. Create credentials file
6. Generate automated deployment script

Then deploy with:

```bash
./deployment/deploy_remote.sh
```

### Option 2: Manual Setup

If you prefer to set everything up manually, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

## Your Setup

Based on your current configuration:

- **SSH Key**: `.secrets/sandiph (1).pem` (already in place ✓)
- **Target**: Remote VM where forecast_agent runs
- **Port**: 8100 (FSGW docs will run here)

## What Happens During Deployment

1. **Connection Test**: Verifies SSH access with your key
2. **Environment Check**: Checks for PM2, uv, forecast_agent
3. **File Transfer**: Copies FSGW code to `/home/ubuntu/fsgateway`
4. **Dependencies**: Installs uv and syncs Python packages
5. **PM2 Service**: Starts `fsgw-docs` on port 8100
6. **Health Check**: Verifies service is responding

## After Deployment

Access the documentation:

```bash
# Create SSH tunnel
ssh -i .secrets/sandiph\ \(1\).pem -L 8100:localhost:8100 <user>@<ip>

# Then open in browser
open http://localhost:8100
```

## Troubleshooting

### SSH Key Issues

If you get permission errors:

```bash
chmod 600 .secrets/sandiph\ \(1\).pem
```

### Connection Issues

Test manually:

```bash
ssh -i .secrets/sandiph\ \(1\).pem <user>@<ip>
```

### Deployment Issues

Check logs on VM:

```bash
ssh -i .secrets/sandiph\ \(1\).pem <user>@<ip> 'pm2 logs fsgw-docs'
```

## PM2 Management

After deployment, manage the service:

```bash
# Check status
ssh <user>@<ip> 'pm2 status'

# View logs
ssh <user>@<ip> 'pm2 logs fsgw-docs'

# Restart
ssh <user>@<ip> 'pm2 restart fsgw-docs'

# Stop
ssh <user>@<ip> 'pm2 stop fsgw-docs'

# Remove
ssh <user>@<ip> 'pm2 delete fsgw-docs && pm2 save'
```

## Safety

This deployment is **100% safe** for your forecast_agent:

- ✅ Different port (8100 vs 5431/3000)
- ✅ Separate PM2 process
- ✅ Independent Python environment
- ✅ Separate logs
- ✅ Can be removed anytime without affecting forecast_agent

## Need Help?

See:
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete deployment guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Advanced options
