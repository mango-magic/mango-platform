#!/bin/bash
# Restart all agents

echo "🔄 Restarting all agents..."

while IFS=',' read -r AGENT_ID IP_ADDRESS; do
    [[ "$AGENT_ID" =~ ^#.*$ ]] && continue
    [ -z "$AGENT_ID" ] && continue
    
    echo "🔄 Restarting $AGENT_ID on $IP_ADDRESS"
    ssh root@$IP_ADDRESS "systemctl restart mango-agent"
    
done < vps-ips.txt

echo "✅ All agents restarted!"

