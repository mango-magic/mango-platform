#!/usr/bin/env python3
"""
Simple monitoring script for The Mangoes
Checks health of all services every 5 minutes
"""

import requests
import time
from datetime import datetime

SERVICES = {
    "Orchestrator": "https://mango-platform.onrender.com",
    "Dashboard": "https://mangoes-dashboard.onrender.com",
}

def check_service(name, url):
    """Check if a service is healthy"""
    try:
        # Try health endpoint
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name}: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"⚠️  {name}: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: Connection failed (service may be down)")
        return False
    except requests.exceptions.Timeout:
        print(f"⏱️  {name}: Timeout (service may be slow)")
        return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def main():
    """Main monitoring loop"""
    print("🥭 The Mangoes - Service Monitor")
    print("Checking services every 5 minutes...\n")
    
    while True:
        print(f"\n{'='*60}")
        print(f"⏰ Check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        all_healthy = True
        for name, url in SERVICES.items():
            healthy = check_service(name, url)
            if not healthy:
                all_healthy = False
        
        if all_healthy:
            print("\n🎉 All services are healthy!")
        else:
            print("\n⚠️  Some services need attention")
        
        print(f"\n💤 Sleeping for 5 minutes...")
        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")

