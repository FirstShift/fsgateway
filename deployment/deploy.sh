#!/bin/bash
set -euo pipefail

# FSGW Documentation Deployment Script
# Deploys FSGW docs to the same VM as forecast_agent

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 FSGW Documentation Deployment${NC}"
echo "================================"
echo ""

# Configuration
VM_HOST="${VM_HOST:-}"
VM_USER="${VM_USER:-ubuntu}"
VM_SSH_PORT="${VM_SSH_PORT:-22}"
FSGW_PORT="${FSGW_PORT:-8100}"
PROJECT_PATH="${PROJECT_PATH:-/home/ubuntu/fsgateway}"

# Check if running on VM or local
if [ -z "$VM_HOST" ]; then
    echo -e "${YELLOW}⚠️  VM_HOST not set. Running locally or already on VM?${NC}"
    read -p "Are you already on the VM? (y/n): " on_vm
    if [ "$on_vm" != "y" ]; then
        echo -e "${RED}❌ Please set VM_HOST environment variable${NC}"
        echo "Example: export VM_HOST=your-vm-hostname"
        exit 1
    fi
    IS_REMOTE=false
else
    IS_REMOTE=true
fi

# Function to run commands (local or remote)
run_command() {
    local cmd="$1"
    if [ "$IS_REMOTE" = true ]; then
        ssh -p "$VM_SSH_PORT" "${VM_USER}@${VM_HOST}" "$cmd"
    else
        eval "$cmd"
    fi
}

echo -e "${BLUE}📋 Configuration:${NC}"
if [ "$IS_REMOTE" = true ]; then
    echo "  VM Host: $VM_HOST"
    echo "  VM User: $VM_USER"
    echo "  SSH Port: $VM_SSH_PORT"
fi
echo "  Project Path: $PROJECT_PATH"
echo "  FSGW Port: $FSGW_PORT"
echo ""

# Check if PM2 is installed
echo -e "${BLUE}🔍 Checking PM2...${NC}"
if run_command "command -v pm2 >/dev/null 2>&1"; then
    echo -e "${GREEN}✅ PM2 is installed${NC}"
else
    echo -e "${YELLOW}⚠️  PM2 not found. Installing...${NC}"
    run_command "npm install -g pm2"
fi

# Check if uv is installed
echo -e "${BLUE}🔍 Checking uv...${NC}"
if run_command "command -v uv >/dev/null 2>&1 || command -v ~/.local/bin/uv >/dev/null 2>&1"; then
    echo -e "${GREEN}✅ uv is installed${NC}"
else
    echo -e "${YELLOW}⚠️  uv not found. Installing...${NC}"
    run_command "curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# Check if project directory exists
echo -e "${BLUE}🔍 Checking project directory...${NC}"
if run_command "[ -d $PROJECT_PATH ]"; then
    echo -e "${GREEN}✅ Project directory exists${NC}"

    echo -e "${BLUE}📥 Pulling latest code...${NC}"
    run_command "cd $PROJECT_PATH && git pull origin main"
else
    echo -e "${YELLOW}⚠️  Project directory not found. Please clone the repository first:${NC}"
    echo "  ssh ${VM_USER}@${VM_HOST} 'cd /home/ubuntu && git clone <repo-url> fsgateway'"
    exit 1
fi

# Check if .env file exists
echo -e "${BLUE}🔍 Checking .env file...${NC}"
if run_command "[ -f $PROJECT_PATH/.env ]"; then
    echo -e "${GREEN}✅ .env file exists${NC}"
else
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create $PROJECT_PATH/.env with:"
    echo ""
    echo "FSGW_GATEWAY_URL=https://dev-cloudgateway.firstshift.ai"
    echo "FSGW_TENANT_ID=7"
    echo "FSGW_USERNAME=your_username"
    echo "FSGW_PASSWORD=your_password"
    exit 1
fi

# Sync dependencies
echo -e "${BLUE}📦 Syncing dependencies...${NC}"
run_command "cd $PROJECT_PATH && \$HOME/.local/bin/uv sync"

# Create logs directory
echo -e "${BLUE}📁 Creating logs directory...${NC}"
run_command "mkdir -p $PROJECT_PATH/logs"

# Check if fsgw-docs is already running
echo -e "${BLUE}🔍 Checking existing deployment...${NC}"
if run_command "pm2 describe fsgw-docs >/dev/null 2>&1"; then
    echo -e "${YELLOW}⚠️  fsgw-docs is already running. Restarting...${NC}"
    run_command "pm2 restart fsgw-docs --update-env"
else
    echo -e "${BLUE}🚀 Starting new deployment...${NC}"
    run_command "pm2 start \"\$HOME/.local/bin/uv run python -m fsgw.server.main --host 0.0.0.0 --port $FSGW_PORT\" \
        --name fsgw-docs \
        --cwd $PROJECT_PATH \
        --output $PROJECT_PATH/logs/fsgw-docs.log \
        --error $PROJECT_PATH/logs/fsgw-docs-error.log"
fi

# Save PM2 configuration
echo -e "${BLUE}💾 Saving PM2 configuration...${NC}"
run_command "pm2 save"

# Wait for service to start
echo -e "${BLUE}⏳ Waiting for service to start...${NC}"
sleep 3

# Health check
echo -e "${BLUE}🏥 Running health check...${NC}"
if run_command "curl -fsS http://localhost:$FSGW_PORT/api/health >/dev/null 2>&1"; then
    echo -e "${GREEN}✅ FSGW docs is responding at http://localhost:$FSGW_PORT${NC}"
else
    echo -e "${RED}❌ Health check failed!${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    run_command "pm2 logs fsgw-docs --lines 20 --nostream"
    exit 1
fi

# Show PM2 status
echo ""
echo -e "${BLUE}📊 PM2 Status:${NC}"
run_command "pm2 status"

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📚 Access the documentation:${NC}"
echo "  Local: http://localhost:$FSGW_PORT"
if [ "$IS_REMOTE" = true ]; then
    echo "  SSH Tunnel: ssh -L 8100:localhost:$FSGW_PORT ${VM_USER}@${VM_HOST}"
fi
echo ""
echo -e "${BLUE}📝 Useful commands:${NC}"
echo "  View logs:    pm2 logs fsgw-docs"
echo "  Restart:      pm2 restart fsgw-docs"
echo "  Stop:         pm2 stop fsgw-docs"
echo "  Remove:       pm2 delete fsgw-docs && pm2 save"
echo ""
