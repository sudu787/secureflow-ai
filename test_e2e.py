import requests
import time
import json

BASE_URL = "http://localhost:8000"

def print_step(step_num, title):
    print(f"\n{'='*50}\n[STEP {step_num}] {title}\n{'='*50}")

def run_test():
    try:
        # 1. Trigger the demo
        print_step(1, "Triggering Operation NightOwl Demo")
        res = requests.post(f"{BASE_URL}/api/demo/start/operation_nightowl")
        print(f"Status Code: {res.status_code}")
        demo_data = res.json()
        print(f"Scenario: {demo_data.get('scenario')}")
        print(f"Alerts created: {demo_data.get('alerts_created')}")
        
        # Wait a moment for agents to process
        time.sleep(2)
        
        # 2. Check Alerts
        print_step(2, "Fetching Alerts (War Room Feed)")
        res = requests.get(f"{BASE_URL}/api/alerts")
        alerts_data = res.json()
        alerts = alerts_data.get("alerts", []) if isinstance(alerts_data, dict) else alerts_data
        print(f"Total alerts fetched: {len(alerts)}")
        if alerts:
            print(f"Sample alert: {alerts[0].get('title')} (Risk: {alerts[0].get('risk_level')})")
            
        # 3. Check Autonomous Pending Actions & XAI Evidence
        print_step(3, "Fetching Pending Actions & XAI Evidence (Autonomous Center)")
        res = requests.get(f"{BASE_URL}/api/autonomous/pending")
        actions_data = res.json()
        actions = actions_data.get("actions", []) if isinstance(actions_data, dict) else actions_data
        print(f"Total pending actions: {len(actions)}")
        
        action_to_approve = None
        for i, a in enumerate(actions):
            print(f"\nAction {i}: {a.get('action')} -> {a.get('target')}")
            xai = a.get("xai_evidence", [])
            if xai:
                print("  [XAI Evidence Found]")
                for ev in xai:
                    print(f"   - {ev.get('icon', '')} {ev.get('label')}: {ev.get('value')} (Source: {ev.get('source')})")
                if not action_to_approve:
                    action_to_approve = i
            else:
                print("  [No dynamic XAI evidence found]")
                
        # 4. Approve an action
        if action_to_approve is not None:
            print_step(4, f"Approving Action Index {action_to_approve}")
            res = requests.post(f"{BASE_URL}/api/autonomous/approve/{action_to_approve}", params={"approved_by": "test_analyst"})
            print(f"Status Code: {res.status_code}")
            print(f"Response: {res.json()}")
        else:
            print_step(4, "Skipping approval (no pending actions)")
            
        # 5. Check Action History
        print_step(5, "Fetching Action History (Execution Log)")
        res = requests.get(f"{BASE_URL}/api/autonomous/history")
        history_data = res.json()
        history = history_data.get("actions", []) if isinstance(history_data, dict) else history_data
        print(f"Total executed actions: {len(history)}")
        if history:
            print(f"Most recent executed: {history[-1].get('action')} [Status: {history[-1].get('status')}]")
            
        # 6. Check Dashboard Stats
        print_step(6, "Fetching Executive Dashboard Stats")
        res = requests.get(f"{BASE_URL}/api/dashboard")
        stats = res.json()
        print(f"Dashboard Stats: {json.dumps(stats, indent=2)}")
        
        print("\n[+] End-to-End Test Completed Successfully!")
        
    except Exception as e:
        print(f"[-] Test Failed: {e}")

if __name__ == '__main__':
    run_test()

