#!/bin/bash
set -euo pipefail

# FSGW Documentation Deployment Setup
# This script helps configure and test the connection to your remote VM

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 FSGW Documentation Deployment Setup${NC}"
echo "========================================"
echo ""

# Prompt for connection details
echo -e "${BLUE}📝 Please provide your VM connection details:${NC}"
echo ""

# VM Host
read -p "VM IP Address or Hostname: " VM_HOST
if [ -z "$VM_HOST" ]; then
    echo -e "${RED}❌ VM host is required${NC}"
    exit 1
fi

# VM User
read -p "VM Username (default: ubuntu): " VM_USER
VM_USER=${VM_USER:-ubuntu}

# SSH Key Path
read -p "Path to SSH private key file: " SSH_KEY_PATH
if [ -z "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ SSH key path is required${NC}"
    exit 1
fi

# Expand ~ to home directory
SSH_KEY_PATH="${SSH_KEY_PATH/#\~/$HOME}"

# Check if key file exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ SSH key file not found: $SSH_KEY_PATH${NC}"
    exit 1
fi

# Check key permissions
KEY_PERMS=$(stat -f "%OLp" "$SSH_KEY_PATH" 2>/dev/null || stat -c "%a" "$SSH_KEY_PATH" 2>/dev/null)
if [ "$KEY_PERMS" != "600" ] && [ "$KEY_PERMS" != "400" ]; then
    echo -e "${YELLOW}⚠️  SSH key has incorrect permissions: $KEY_PERMS${NC}"
    echo -e "${BLUE}Fixing permissions...${NC}"
    chmod 600 "$SSH_KEY_PATH"
    echo -e "${GREEN}✅ Key permissions set to 600${NC}"
fi

# SSH Port
read -p "SSH Port (default: 22): " SSH_PORT
SSH_PORT=${SSH_PORT:-22}

echo ""
echo -e "${BLUE}📋 Connection Configuration:${NC}"
echo "  Host: $VM_HOST"
echo "  User: $VM_USER"
echo "  Key:  $SSH_KEY_PATH"
echo "  Port: $SSH_PORT"
echo ""

# Test SSH connection
echo -e "${BLUE}🔌 Testing SSH connection...${NC}"
if ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" -o ConnectTimeout=10 -o BatchMode=yes "${VM_USER}@${VM_HOST}" "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection successful!${NC}"
else
    echo -e "${RED}❌ SSH connection failed!${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "1. Verify the IP address is correct: $VM_HOST"
    echo "2. Verify the username is correct: $VM_USER"
    echo "3. Verify the SSH key file is correct: $SSH_KEY_PATH"
    echo "4. Verify the port is correct: $SSH_PORT"
    echo "5. Try connecting manually:"
    echo "   ssh -i $SSH_KEY_PATH -p $SSH_PORT ${VM_USER}@${VM_HOST}"
    exit 1
fi

# Check system info
echo ""
echo -e "${BLUE}🖥️  Checking VM system info...${NC}"
ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${VM_USER}@${VM_HOST}" "uname -a"

# Check if forecast_agent is running
echo ""
echo -e "${BLUE}🔍 Checking for forecast_agent deployment...${NC}"
if ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${VM_USER}@${VM_HOST}" "[ -d /home/ubuntu/forecast_agent ]" 2>/dev/null; then
    echo -e "${GREEN}✅ forecast_agent directory found${NC}"

    # Check PM2 processes
    if ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${VM_USER}@${VM_HOST}" "command -v pm2 >/dev/null 2>&1" 2>/dev/null; then
        echo -e "${GREEN}✅ PM2 is installed${NC}"
        echo ""
        echo -e "${BLUE}📊 Current PM2 processes:${NC}"
        ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${VM_USER}@${VM_HOST}" "pm2 status" || echo -e "${YELLOW}⚠️  Could not get PM2 status${NC}"
    else
        echo -e "${YELLOW}⚠️  PM2 not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  forecast_agent directory not found at /home/ubuntu/forecast_agent${NC}"
    echo "   This is OK if forecast_agent is in a different location"
fi

# Check if fsgateway already exists
echo ""
echo -e "${BLUE}🔍 Checking if fsgateway is already deployed...${NC}"
if ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${VM_USER}@${VM_HOST}" "[ -d /home/ubuntu/fsgateway ]" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  fsgateway directory already exists${NC}"
    read -p "Do you want to remove it and redeploy? (y/n): " REMOVE_EXISTING
    if [ "$REMOVE_EXISTING" = "y" ]; then
        echo -e "${BLUE}🗑️  Removing existing fsgateway...${NC}"
        ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${VM_USER}@${VM_HOST}" "rm -rf /home/ubuntu/fsgateway"
        echo -e "${GREEN}✅ Removed existing installation${NC}"
    fi
else
    echo -e "${GREEN}✅ No existing fsgateway installation found${NC}"
fi

# Save configuration to .deploy_config file
echo ""
echo -e "${BLUE}💾 Saving configuration...${NC}"
cat > .deploy_config << EOF
# FSGW Deployment Configuration
# Generated: $(date)
export VM_HOST="$VM_HOST"
export VM_USER="$VM_USER"
export SSH_KEY_PATH="$SSH_KEY_PATH"
export SSH_PORT="$SSH_PORT"
EOF

chmod 600 .deploy_config
echo -e "${GREEN}✅ Configuration saved to .deploy_config${NC}"

# Prompt for FirstShift credentials
echo ""
echo -e "${BLUE}🔑 FirstShift Gateway Credentials${NC}"
echo "These will be stored in .env.remote (not committed to git)"
echo ""

read -p "FSGW Username: " FSGW_USERNAME
if [ -z "$FSGW_USERNAME" ]; then
    echo -e "${RED}❌ Username is required${NC}"
    exit 1
fi

read -sp "FSGW Password: " FSGW_PASSWORD
echo ""
if [ -z "$FSGW_PASSWORD" ]; then
    echo -e "${RED}❌ Password is required${NC}"
    exit 1
fi

# Save credentials to .env.remote
cat > .env.remote << EOF
FSGW_GATEWAY_URL=https://dev-cloudgateway.firstshift.ai
FSGW_TENANT_ID=7
FSGW_USERNAME=$FSGW_USERNAME
FSGW_PASSWORD=$FSGW_PASSWORD
EOF

chmod 600 .env.remote
echo -e "${GREEN}✅ Credentials saved to .env.remote${NC}"

# Create deployment helper script
echo ""
echo -e "${BLUE}📝 Creating deployment helper script...${NC}"
cat > deploy_remote.sh << 'EOFSCRIPT'
#!/bin/bash
set -euo pipefail

# Load configuration
if [ ! -f .deploy_config ]; then
    echo "❌ Configuration file not found. Run ./setup_deployment.sh first"
    exit 1
fi

source .deploy_config

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Deploying FSGW Documentation to Remote VM${NC}"
echo "=============================================="
echo ""

# Copy repository to VM
echo -e "${BLUE}📤 Copying files to VM...${NC}"
ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${VM_USER}@${VM_HOST}" "mkdir -p /home/ubuntu/fsgateway"

rsync -avz -e "ssh -i $SSH_KEY_PATH -p $SSH_PORT" \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='.mypy_cache' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='.deploy_config' \
    --exclude='.env.remote' \
    ./ "${VM_USER}@${VM_HOST}:/home/ubuntu/fsgateway/"

echo -e "${GREEN}✅ Files copied${NC}"

# Copy .env file
echo -e "${BLUE}📤 Copying .env file...${NC}"
scp -i "$SSH_KEY_PATH" -P "$SSH_PORT" .env.remote "${VM_USER}@${VM_HOST}:/home/ubuntu/fsgateway/.env"

# Run deployment
echo -e "${BLUE}🚀 Running deployment on VM...${NC}"
ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${VM_USER}@${VM_HOST}" << 'EOFSSH'
set -euo pipefail

cd /home/ubuntu/fsgateway

# Install uv if needed
if ! command -v uv >/dev/null 2>&1 && ! command -v ~/.local/bin/uv >/dev/null 2>&1; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

export PATH="$HOME/.local/bin:$PATH"

# Sync dependencies
echo "📦 Syncing dependencies..."
uv sync

# Create logs directory
mkdir -p logs

# Install PM2 if needed
if ! command -v pm2 >/dev/null 2>&1; then
    echo "📦 Installing PM2..."
    npm install -g pm2
fi

# Deploy with PM2
echo "🚀 Deploying with PM2..."
if pm2 describe fsgw-docs >/dev/null 2>&1; then
    echo "⚙️  Restarting existing deployment..."
    pm2 restart fsgw-docs --update-env
else
    echo "🆕 Starting new deployment..."
    pm2 start "$HOME/.local/bin/uv run python -m fsgw.server.main --host 0.0.0.0 --port 8100" \
        --name fsgw-docs \
        --cwd /home/ubuntu/fsgateway \
        --output /home/ubuntu/fsgateway/logs/fsgw-docs.log \
        --error /home/ubuntu/fsgateway/logs/fsgw-docs-error.log
fi

pm2 save

# Wait and health check
echo "⏳ Waiting for service to start..."
sleep 3

if curl -fsS http://localhost:8100/api/health >/dev/null 2>&1; then
    echo "✅ Health check passed"
    pm2 status
else
    echo "❌ Health check failed"
    pm2 logs fsgw-docs --lines 20 --nostream
    exit 1
fi
EOFSSH

echo ""
echo -e "${GREEN}🎉 Deployment completed!${NC}"
echo ""
echo -e "${BLUE}📚 Access the documentation:${NC}"
echo "  Via SSH tunnel: ssh -i $SSH_KEY_PATH -p $SSH_PORT -L 8100:localhost:8100 ${VM_USER}@${VM_HOST}"
echo "  Then open: http://localhost:8100"
echo ""
echo -e "${BLUE}📝 Useful commands:${NC}"
echo "  View logs:  ssh -i $SSH_KEY_PATH -p $SSH_PORT ${VM_USER}@${VM_HOST} 'pm2 logs fsgw-docs'"
echo "  PM2 status: ssh -i $SSH_KEY_PATH -p $SSH_PORT ${VM_USER}@${VM_HOST} 'pm2 status'"
echo "  Restart:    ssh -i $SSH_KEY_PATH -p $SSH_PORT ${VM_USER}@${VM_HOST} 'pm2 restart fsgw-docs'"
echo ""
EOFSCRIPT

chmod +x deploy_remote.sh
echo -e "${GREEN}✅ Created deploy_remote.sh${NC}"

# Summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📝 What was created:${NC}"
echo "  • .deploy_config       - VM connection settings"
echo "  • .env.remote          - FirstShift credentials"
echo "  • deploy_remote.sh     - Automated deployment script"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo ""
echo -e "${GREEN}1. Deploy to VM:${NC}"
echo "   ./deploy_remote.sh"
echo ""
echo -e "${GREEN}2. Access documentation:${NC}"
echo "   ssh -i $SSH_KEY_PATH -p $SSH_PORT -L 8100:localhost:8100 ${VM_USER}@${VM_HOST}"
echo "   Then open: http://localhost:8100"
echo ""
echo -e "${YELLOW}⚠️  Security note:${NC}"
echo "   .deploy_config and .env.remote contain sensitive data"
echo "   They are in .gitignore and will NOT be committed"
echo ""
