#!/bin/bash
# Deploy FSGW Documentation Server to Staging VM
# Target: ubuntu@52.53.245.194 (agents-staging)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/.secrets/deployment_config.sh"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file not found at $CONFIG_FILE${NC}"
    exit 1
fi

source "$CONFIG_FILE"

echo -e "${GREEN}=== FSGW Deployment to Staging ===${NC}"
echo "Target: $VM_USER@$VM_HOST"
echo "Port: $FSGW_PORT"
echo "Project path: $PROJECT_PATH"
echo

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ! ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$VM_USER@$VM_HOST" "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to $VM_USER@$VM_HOST${NC}"
    echo
    echo "Troubleshooting steps:"
    echo "1. Verify the SSH key is correct: $SSH_KEY_PATH"
    echo "2. Check key permissions: chmod 600 $SSH_KEY_PATH"
    echo "3. Verify your public key is in ~/.ssh/authorized_keys on the server"
    echo "4. Test manually: ssh -i $SSH_KEY_PATH $VM_USER@$VM_HOST"
    echo
    echo "To add your public key to the server, run:"
    echo "  ssh-keygen -y -f $SSH_KEY_PATH"
    echo "Then add the output to ~/.ssh/authorized_keys on the server"
    exit 1
fi

echo -e "${GREEN}✓ SSH connection successful${NC}"
echo

# Check if project directory exists
echo -e "${YELLOW}Checking remote environment...${NC}"
ssh -i "$SSH_KEY_PATH" "$VM_USER@$VM_HOST" bash <<'REMOTE_CHECK'
    echo "Hostname: $(hostname)"
    echo "User: $(whoami)"
    echo "Home: $HOME"
    echo "Python: $(python3 --version 2>/dev/null || echo 'Not installed')"
    echo "Node: $(node --version 2>/dev/null || echo 'Not installed')"
    echo "PM2: $(pm2 --version 2>/dev/null || echo 'Not installed')"
REMOTE_CHECK

echo

# Create project directory if it doesn't exist
echo -e "${YELLOW}Preparing project directory...${NC}"
ssh -i "$SSH_KEY_PATH" "$VM_USER@$VM_HOST" "mkdir -p $PROJECT_PATH"

# Sync project files (excluding .git, node_modules, __pycache__, etc.)
echo -e "${YELLOW}Syncing project files...${NC}"
rsync -avz --progress \
    -e "ssh -i $SSH_KEY_PATH" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='.ruff_cache' \
    --exclude='.mypy_cache' \
    --exclude='.env' \
    --exclude='.secrets' \
    --exclude='.discovery' \
    "$PROJECT_ROOT/" \
    "$VM_USER@$VM_HOST:$PROJECT_PATH/"

echo -e "${GREEN}✓ Files synced${NC}"
echo

# Create .env file on remote
echo -e "${YELLOW}Creating .env file on remote...${NC}"
ssh -i "$SSH_KEY_PATH" "$VM_USER@$VM_HOST" bash <<REMOTE_ENV
cat > $PROJECT_PATH/.env <<'EOF'
FSGW_GATEWAY_URL=$FSGW_GATEWAY_URL
FSGW_TENANT_ID=$FSGW_TENANT_ID
FSGW_USERNAME=$FSGW_USERNAME
FSGW_PASSWORD=$FSGW_PASSWORD
EOF
REMOTE_ENV

echo -e "${GREEN}✓ .env file created${NC}"
echo

# Install dependencies and setup
echo -e "${YELLOW}Installing dependencies on remote...${NC}"
ssh -i "$SSH_KEY_PATH" "$VM_USER@$VM_HOST" bash <<REMOTE_INSTALL
    cd $PROJECT_PATH

    # Install uv if not present
    if ! command -v uv &> /dev/null; then
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="\$HOME/.cargo/bin:\$PATH"
    fi

    # Sync dependencies
    echo "Installing Python dependencies..."
    uv sync

    # Install PM2 locally if not present
    if ! command -v pm2 &> /dev/null && [ ! -f node_modules/.bin/pm2 ]; then
        echo "Installing PM2 locally..."
        npm install pm2
    fi
REMOTE_INSTALL

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo

# Stop existing PM2 process if running
echo -e "${YELLOW}Stopping existing service...${NC}"
ssh -i "$SSH_KEY_PATH" "$VM_USER@$VM_HOST" bash <<REMOTE_STOP
    cd $PROJECT_PATH
    if [ -f node_modules/.bin/pm2 ]; then
        node_modules/.bin/pm2 delete fsgw-docs || true
    elif command -v pm2 &> /dev/null; then
        pm2 delete fsgw-docs || true
    fi
REMOTE_STOP

echo -e "${GREEN}✓ Existing service stopped${NC}"
echo

# Start the service with PM2
echo -e "${YELLOW}Starting FSGW documentation server...${NC}"
ssh -i "$SSH_KEY_PATH" "$VM_USER@$VM_HOST" bash <<REMOTE_START
    cd $PROJECT_PATH

    # Determine PM2 command
    if [ -f node_modules/.bin/pm2 ]; then
        PM2="node_modules/.bin/pm2"
    else
        PM2="pm2"
    fi

    # Start the service
    \$PM2 start --name fsgw-docs \
        --interpreter none \
        -- bash -c "source \$HOME/.cargo/env 2>/dev/null || true && uv run python -m fsgw.server.main --port $FSGW_PORT"

    # Save PM2 configuration
    \$PM2 save || true

    # Show status
    echo
    \$PM2 list
    echo
    \$PM2 logs fsgw-docs --lines 20 --nostream
REMOTE_START

echo
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo
echo "Service is running on port $FSGW_PORT"
echo
echo "To access the documentation:"
echo "  1. Create SSH tunnel: ssh -L 8100:localhost:$FSGW_PORT -i $SSH_KEY_PATH $VM_USER@$VM_HOST"
echo "  2. Open browser: http://localhost:8100"
echo
echo "To view logs:"
echo "  ssh -i $SSH_KEY_PATH $VM_USER@$VM_HOST 'cd $PROJECT_PATH && pm2 logs fsgw-docs'"
echo
echo "To stop the service:"
echo "  ssh -i $SSH_KEY_PATH $VM_USER@$VM_HOST 'cd $PROJECT_PATH && pm2 stop fsgw-docs'"
echo
