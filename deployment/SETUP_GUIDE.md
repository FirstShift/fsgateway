# Remote Deployment Setup Guide

## Overview

This guide will help you deploy the FSGW documentation website to your remote VM where forecast_agent is running.

## What You Need

Before starting, have these ready:

1. ✅ **VM IP Address or Hostname** - The server IP (e.g., `192.168.1.100` or `myserver.example.com`)
2. ✅ **SSH Username** - Your login username (e.g., `ubuntu`)
3. ✅ **SSH Private Key File** - The permission/key file for authentication (e.g., `~/Downloads/my-key.pem`)
4. ✅ **FirstShift Gateway Credentials** - Your FSGW username and password
5. ✅ **SSH Port** - Usually `22` (default)

## Step-by-Step Deployment

### Step 1: Run the Setup Script

The setup script will:
- Test your SSH connection
- Check the VM system
- Verify forecast_agent is running
- Save your configuration securely
- Create an automated deployment script

```bash
cd /Users/al/Projects/firstshift/fsgateway
./setup_deployment.sh
```

**You'll be prompted for:**

1. **VM IP Address or Hostname**: Enter your server's IP or hostname
   - Example: `192.168.1.100` or `myserver.com`

2. **VM Username**: Enter your SSH username (default: ubuntu)
   - Just press Enter if it's `ubuntu`

3. **Path to SSH private key file**: Enter the full path to your .pem or key file
   - Example: `~/Downloads/my-key.pem` or `/Users/al/.ssh/id_rsa`

4. **SSH Port**: Enter the SSH port (default: 22)
   - Just press Enter if it's the default port 22

5. **FSGW Username**: Your FirstShift Gateway username

6. **FSGW Password**: Your FirstShift Gateway password (hidden as you type)

### Step 2: Review the Connection Test

The script will:
- ✅ Test SSH connection
- ✅ Check VM system information
- ✅ Verify forecast_agent is running
- ✅ Check PM2 processes
- ✅ Save configuration files

If any step fails, the script will provide troubleshooting tips.

### Step 3: Deploy to VM

Once setup is complete, deploy with one command:

```bash
./deploy_remote.sh
```

This will:
1. Copy all files to the VM
2. Copy your credentials (.env file)
3. Install dependencies (uv, PM2 if needed)
4. Start the documentation service on port 8100
5. Run health checks

### Step 4: Access the Documentation

**Option A: SSH Tunnel (Recommended)**

Open an SSH tunnel to access the documentation locally:

```bash
# This command will be shown at the end of deployment
ssh -i <your-key-path> -p <port> -L 8100:localhost:8100 <user>@<host>
```

Then open in your browser: **http://localhost:8100**

**Option B: Configure Reverse Proxy**

If you have nginx/caddy on the VM, you can expose it at a public URL (see DEPLOYMENT.md for config examples).

## What Gets Created

After running `setup_deployment.sh`, you'll have:

- **`.deploy_config`** - SSH connection settings (gitignored)
- **`.env.remote`** - FirstShift credentials (gitignored)
- **`deploy_remote.sh`** - Automated deployment script (gitignored)

**These files contain sensitive data and are automatically excluded from git.**

## PM2 Services on Your VM

After deployment:

```
PM2 Services:
├── backend        (Port 5431) - forecast_agent backend
├── frontend       (Port 3000) - forecast_agent frontend
└── fsgw-docs      (Port 8100) - FSGW Documentation ← NEW
```

## Common Commands

### View Documentation Logs
```bash
ssh -i <key-path> -p <port> <user>@<host> 'pm2 logs fsgw-docs'
```

### Check PM2 Status
```bash
ssh -i <key-path> -p <port> <user>@<host> 'pm2 status'
```

### Restart Documentation Service
```bash
ssh -i <key-path> -p <port> <user>@<host> 'pm2 restart fsgw-docs'
```

### Stop Documentation Service
```bash
ssh -i <key-path> -p <port> <user>@<host> 'pm2 stop fsgw-docs'
```

### Remove Documentation Service
```bash
ssh -i <key-path> -p <port> <user>@<host> 'pm2 delete fsgw-docs && pm2 save'
```

### Update/Redeploy
```bash
# Just run the deployment script again
./deploy_remote.sh
```

## Troubleshooting

### SSH Connection Fails

**Problem**: "SSH connection failed" error during setup

**Solutions**:
1. Verify IP address is correct
2. Check SSH key file path is correct
3. Ensure key has correct permissions (600)
4. Try manual connection:
   ```bash
   ssh -i <key-path> -p <port> <user>@<host>
   ```

### Key Permission Issues

**Problem**: "WARNING: UNPROTECTED PRIVATE KEY FILE"

**Solution**: The script will auto-fix this, or run manually:
```bash
chmod 600 <path-to-key-file>
```

### Service Won't Start

**Problem**: Deployment succeeds but health check fails

**Solutions**:
1. Check logs:
   ```bash
   ssh -i <key-path> -p <port> <user>@<host> 'pm2 logs fsgw-docs'
   ```
2. Verify .env file has correct credentials
3. Check if port 8100 is already in use:
   ```bash
   ssh -i <key-path> -p <port> <user>@<host> 'sudo lsof -i :8100'
   ```

### Can't Access Documentation

**Problem**: SSH tunnel established but can't access http://localhost:8100

**Solutions**:
1. Verify service is running:
   ```bash
   ssh -i <key-path> -p <port> <user>@<host> 'pm2 status fsgw-docs'
   ```
2. Check health endpoint on VM:
   ```bash
   ssh -i <key-path> -p <port> <user>@<host> 'curl http://localhost:8100/api/health'
   ```
3. Verify SSH tunnel is active (look for the ssh process)

## Safety Notes

✅ **Completely Safe**: This deployment:
- Uses a separate port (8100) from forecast_agent
- Runs as an independent PM2 process
- Has its own Python environment (uv)
- Can be removed without affecting forecast_agent
- Read-only service with minimal resources

✅ **Forecast Agent Unaffected**: Your mission-critical forecast_agent services (`backend` on 5431, `frontend` on 3000) will continue running normally.

## Files Created on VM

```
/home/ubuntu/fsgateway/
├── fsgw/                  # Python package
├── .env                   # Credentials (from .env.remote)
├── logs/                  # Log files
│   ├── fsgw-docs.log
│   └── fsgw-docs-error.log
└── [other files]
```

## Quick Reference

| Task | Command |
|------|---------|
| Setup & test connection | `./setup_deployment.sh` |
| Deploy to VM | `./deploy_remote.sh` |
| Access docs | `ssh -i <key> -L 8100:localhost:8100 <user>@<host>` |
| View logs | `ssh <user>@<host> 'pm2 logs fsgw-docs'` |
| Restart service | `ssh <user>@<host> 'pm2 restart fsgw-docs'` |
| Remove service | `ssh <user>@<host> 'pm2 delete fsgw-docs'` |

## Need Help?

1. Check PM2 logs for errors
2. Verify .env credentials are correct
3. Ensure forecast_agent is running properly first
4. Test manual SSH connection
5. Check if uv and PM2 are installed on VM

---

**Ready to deploy?** Start with `./setup_deployment.sh`!
