import requests
import sys
import time

print("========================================")
print("🩺 SecureFlow AI Health Check")
print("========================================\n")

services = {
    "Backend API (Port 8000)": "http://localhost:8000/docs",
    "Frontend UI (Port 3000)": "http://localhost:3000"
}

all_healthy = True

for name, url in services.items():
    print(f"Checking {name}...", end=" ")
    try:
        # Give a small timeout since frontend can take a moment to compile on first hit
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            print("✅ ONLINE")
        else:
            print(f"⚠️ HTTP {res.status_code}")
            all_healthy = False
    except requests.exceptions.ConnectionError:
        print("❌ OFFLINE")
        all_healthy = False

print("\n" + "="*40)
if all_healthy:
    print("🚀 All systems GO! The platform is ready for the demo.")
    sys.exit(0)
else:
    print("⚠️  Some systems are offline. Did you run setup.sh?")
    sys.exit(1)
