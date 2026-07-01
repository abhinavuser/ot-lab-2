# Railroad North - Instructor Guide

## Workshop Timeline

### Day 1: Guided Exploration (4 hours)

| Time | Activity | Duration |
|---|---|---|
| 0:00 - 0:30 | Lecture: OT vs IT, Purdue Model, Lab Architecture | 30 min |
| 0:30 - 0:45 | Setup: `docker-compose up -d`, verify all 8 containers | 15 min |
| 0:45 - 1:15 | Demo: Walk through the SCADA Dashboard, explain each panel | 30 min |
| 1:15 - 1:45 | Scenario 1: Unauthorized Track Switching (guided) | 30 min |
| 1:45 - 2:15 | Scenario 2: Heartbeat Failure / DoS (guided) | 30 min |
| 2:15 - 2:30 | Break | 15 min |
| 2:30 - 3:00 | Scenario 3: Alarm Flooding (guided) | 30 min |
| 3:00 - 3:30 | Scenario 4: Safety Interlock Validation (guided) | 30 min |
| 3:30 - 4:00 | Wireshark Intro: Capture traffic during an attack | 30 min |

### Day 2: Capture The Flag (4 hours)

| Time | Activity | Duration |
|---|---|---|
| 0:00 - 0:15 | Recap Day 1, explain CTF rules, form teams | 15 min |
| 0:15 - 0:30 | Open CTF Scoreboard, register teams | 15 min |
| 0:30 - 3:30 | CTF Competition (8 challenges, self-paced) | 3 hours |
| 3:30 - 4:00 | Scoreboard reveal, winning team, debrief | 30 min |

## Before the Workshop

1. Ensure Docker Desktop is installed on all student machines.
2. Pre-pull the images to avoid slow downloads during class:
   ```bash
   docker pull python:3.11-slim
   docker pull lscr.io/linuxserver/wireshark:latest
   ```
3. Test the full lab on your machine:
   ```bash
   docker-compose up -d
   docker ps   # Should show 8 containers
   ```
4. Open `http://localhost:8081` (SCADA), `http://localhost:8090` (CTF), `http://localhost:3000` (Wireshark) to verify all are accessible.

## Key Talking Points

### When Explaining the Dashboard
- The 3 segments represent physical sections of track: North Entrance, Central Junction, South Yard.
- Routes A/B/C represent which physical track the junction switch is pointing to.
- The yellow highlighted button shows the currently active route.
- Green entries in the Audit Log = legitimate operator commands.
- Yellow entries = unauthorized API calls (attacks).
- Red entries = commands rejected by safety interlocks.

### When Explaining the Heartbeat Demo
- After running `docker stop railroad-slave-plc-1`, DO NOT PANIC when nothing happens immediately.
- The Master PLC needs 3 missed heartbeats (15-20 seconds) before triggering E-STOP.
- Use this delay as a teaching moment: explain why real systems have a tolerance window to avoid false positives from momentary network glitches.

### When Explaining the CTF
- The flags are real values extracted from the live system. Students must actually interact with the APIs and Wireshark to find them.
- The "forensics-1" challenge has a dynamic flag; any number >= 50 is accepted (since the flood attack sends 50 commands).
- Hints cost -50 points. Encourage teams to try without hints first.

## CTF Answer Key (DO NOT SHARE WITH STUDENTS)

| Challenge | Flag | How to Find It |
|---|---|---|
| recon-1 | `172.25.0.10` | Filter Wireshark for HTTP responses from /api/status |
| recon-2 | `502` | Read docker-compose.yml or check Modbus port mapping |
| exploit-1 | `ROUTE_C` | POST to /api/command and read the `requested_route` response field |
| exploit-2 | `Occupancy North` | POST to /api/device/set and read the `device` response field |
| forensics-1 | Any number >= 50 | GET /api/status after the flood and read `total_commands` |
| forensics-2 | `segment_id` | Follow the TCP stream in Wireshark, read the JSON POST body |
| defense-1 | `emergency_cleared` | POST to /api/emergency/clear and read the `action` response field |
| defense-2 | `Conflicting routes at junction` | Set both Seg 1 and Seg 2 to ROUTE_A, read the rejection reason |

## Troubleshooting During Class

| Student Issue | Quick Fix |
|---|---|
| "Dashboard is blank" | `docker restart railroad-scada`, wait 10 seconds |
| "Attack script says ModuleNotFoundError" | They are running the old script. Pull the latest version |
| "Wireshark won't load" | The image is ~500MB; check if it is still downloading with `docker pull lscr.io/linuxserver/wireshark:latest` |
| "Clear Faults does nothing" | Slave PLC is still stopped. Run `docker start railroad-slave-plc-1` first |
| "CTF flag is wrong" | Double check exact capitalization and spelling. Flags are case-insensitive but must match the exact string |
| "Docker out of memory" | Close other applications. The lab needs ~4GB RAM for all 8 containers |
