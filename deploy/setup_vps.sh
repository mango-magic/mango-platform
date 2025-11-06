#!/bin/bash
# Complete VPS setup script - run this on each VPS

set -e

echo "🥭 ManyMangoes VPS Setup"
echo "========================"

# Get agent ID from environment or prompt
AGENT_ID=${1:-""}
if [ -z "$AGENT_ID" ]; then
    read -p "Enter Agent ID (e.g., backend_001): " AGENT_ID
fi

echo "Setting up VPS for: $AGENT_ID"

# Update system
echo "📦 Updating system..."
apt-get update && apt-get upgrade -y

# Install essential packages
echo "📦 Installing packages..."
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    curl \
    wget \
    tmux \
    htop \
    nginx \
    postgresql-14 \
    redis-server \
    chromium-browser \
    chromium-chromedriver \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2

# Create mango user
echo "👤 Creating mango user..."
useradd -m -s /bin/bash mango || true
mkdir -p /opt/mango
chown -R mango:mango /opt/mango

# Switch to mango user for remaining setup
su - mango << 'EOF'

# Setup Python environment
echo "🐍 Setting up Python environment..."
cd /opt/mango
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install \
    google-generativeai \
    playwright \
    aiohttp \
    asyncio \
    psycopg2-binary \
    redis \
    fastapi \
    uvicorn \
    gitpython \
    python-dotenv

# Install Playwright browsers
playwright install chromium

# Clone repository
echo "📥 Cloning repository..."
cd /opt/mango
if [ ! -d "mango-platform" ]; then
    git clone https://github.com/mango-magic/mango-platform.git
fi

cd mango-platform
git pull origin main

# Create necessary directories
mkdir -p logs data/tasks data/state config

# Create .env file
cat > .env << ENVEOF
AGENT_ID=${AGENT_ID}
GEMINI_API_KEY=${GEMINI_API_KEY}
GITHUB_TOKEN=${GITHUB_TOKEN}
TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
DATABASE_URL=postgresql://mango:mango@localhost/mango
REDIS_URL=redis://localhost:6379
ENVEOF

# Setup systemd service
EOF

# Create systemd service (as root)
cat > /etc/systemd/system/mango-agent.service << SERVICEEOF
[Unit]
Description=ManyMangoes Agent - ${AGENT_ID}
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=mango
WorkingDirectory=/opt/mango/mango-platform
Environment="PATH=/opt/mango/venv/bin"
ExecStart=/opt/mango/venv/bin/python core/orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Enable and start service
systemctl daemon-reload
systemctl enable mango-agent
systemctl start mango-agent

echo ""
echo "✅ Setup complete for ${AGENT_ID}!"
echo ""
echo "📊 Status: systemctl status mango-agent"
echo "📋 Logs: journalctl -u mango-agent -f"
echo "🔄 Restart: systemctl restart mango-agent"

