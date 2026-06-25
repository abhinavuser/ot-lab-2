#!/usr/bin/env python3
"""
Railroad North - Traffic Generator
Generates normal and anomalous traffic for testing
"""

import requests
import time
import sys
import random

SCADA_URL = "http://localhost:8080"
MASTER_URL = "http://localhost:8085"

ROUTES = ["ROUTE_A", "ROUTE_B", "ROUTE_C"]
SEGMENTS = [1, 2, 3]


def normal_traffic(count=10, delay=2):
    """Generate normal operational traffic"""
    print("=" * 50)
    print("NORMAL TRAFFIC GENERATION")
    print("=" * 50)
    
    for i in range(count):
        seg = SEGMENTS[i % 3]
        route = ROUTES[i % 3]
        try:
            resp = requests.post(
                f"{MASTER_URL}/api/command",
                json={"segment_id": seg, "route": route},
                timeout=2
            )
            result = resp.json()
            status = "✓" if result.get('success') else "✗"
            print(f"  [{status}] Command {i+1}: Segment {seg} -> {route}")
        except Exception as e:
            print(f"  [!] Command {i+1} failed: {e}")
        time.sleep(delay)


def rapid_fire_traffic(count=20, delay=0.1):
    """Generate rapid-fire traffic (potential attack pattern)"""
    print("\n" + "=" * 50)
    print("RAPID-FIRE TRAFFIC (Attack Pattern)")
    print("=" * 50)
    
    for i in range(count):
        try:
            resp = requests.post(
                f"{MASTER_URL}/api/command",
                json={"segment_id": 1, "route": "ROUTE_A"},
                timeout=2
            )
            print(f"  Rapid command {i+1}/{count}")
        except Exception as e:
            print(f"  [!] Failed: {e}")
        time.sleep(delay)


def status_check():
    """Check current system status"""
    print("\n" + "=" * 50)
    print("SYSTEM STATUS")
    print("=" * 50)
    
    try:
        resp = requests.get(f"{MASTER_URL}/api/status", timeout=2)
        data = resp.json()
        for seg in data.get('segments', []):
            print(f"  Segment {seg['segment_id']}: {seg['name']}")
            print(f"    State: {seg['state']}, Route: {seg.get('current_route', 'NONE')}")
            print(f"    Signal: {seg['signal_state']}, Occupied: {seg['sensor_occupied']}")
        print(f"\n  Total commands: {data.get('total_commands', 0)}")
    except Exception as e:
        print(f"  [!] Cannot reach Master PLC: {e}")


if __name__ == '__main__':
    print("╔════════════════════════════════════════════════╗")
    print("║   Railroad North - Traffic Generator           ║")
    print("╚════════════════════════════════════════════════╝")
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if mode in ("normal", "all"):
        normal_traffic()
    if mode in ("rapid", "all"):
        rapid_fire_traffic()
    
    status_check()
    print("\nTraffic generation complete.")
