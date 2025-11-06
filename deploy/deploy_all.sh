#!/bin/bash
# Master deployment script - deploys to all VPS servers

set -e

echo "🥭 ManyMangoes Multi-VPS Deployment"
echo "===================================="
echo ""

# Check for required files
if [ ! -f "vps-ips.txt" ]; then
    echo "❌ Error: vps-ips.txt not found"
    echo "Create this file with format: AGENT_ID,IP_ADDRESS"
    exit 1
fi

# Check for required env vars
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY not set"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Error: GITHUB_TOKEN not set"
    exit 1
fi

if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "❌ Error: TELEGRAM_TOKEN not set"
    exit 1
fi

# Read SSH key
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

echo "📋 Deploying to all VPS servers..."
echo ""

# Counter
SUCCESS=0
FAILED=0

# Deploy to each VPS
while IFS=',' read -r AGENT_ID IP_ADDRESS; do
    # Skip comments and empty lines
    [[ "$AGENT_ID" =~ ^#.*$ ]] && continue
    [ -z "$AGENT_ID" ] && continue
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Deploying: $AGENT_ID to $IP_ADDRESS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Copy setup script to VPS
    scp -i $SSH_KEY deploy/setup_vps.sh root@$IP_ADDRESS:/tmp/
    
    # Run setup script
    ssh -i $SSH_KEY root@$IP_ADDRESS "export AGENT_ID=$AGENT_ID \
        GEMINI_API_KEY=$GEMINI_API_KEY \
        GITHUB_TOKEN=$GITHUB_TOKEN \
        TELEGRAM_TOKEN=$TELEGRAM_TOKEN \
        TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID && \
        bash /tmp/setup_vps.sh $AGENT_ID"
    
    if [ $? -eq 0 ]; then
        echo "✅ $AGENT_ID deployed successfully"
        ((SUCCESS++))
    else
        echo "❌ $AGENT_ID deployment failed"
        ((FAILED++))
    fi
    
    echo ""
    
done < vps-ips.txt

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Deployment Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Successful: $SUCCESS"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All agents deployed successfully!"
    echo ""
    echo "🔥 The autonomous AI team is now building 24 Mangoes!"
    echo ""
    echo "📊 Monitor progress:"
    echo "   - Dashboard: http://[ORCHESTRATOR_IP]:8080"
    echo "   - Logs: ssh root@[IP] 'journalctl -u mango-agent -f'"
    echo ""
else
    echo "⚠️  Some deployments failed. Check errors above."
fi

