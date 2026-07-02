# Railroad North - Comprehensive Instructor & Lab Guide
**Duration**: 16 Hours (2 Days, 8 Hours/Day)
**Version**: 2.0 (AWS SOC & Local Parity)

This is the ultimate, single-source-of-truth document for the Railroad North OT Security Workshop. It contains the 16-hour timeline, complete walkthroughs of every attack (with exact codes/commands), and the full CTF answer key with explanations.

---

## 📅 Workshop Timeline (16 Hours)

### Day 1: Foundation & Threat Execution (8 Hours)
**Focus:** Understanding OT networks, the Purdue Model, and executing cyber-physical attacks.
- **09:00 - 10:30 (1.5h):** Theory - IT vs OT differences, Purdue Model, PLC architecture.
- **10:30 - 11:30 (1.0h):** Lab Setup & Dashboard Walkthrough. (Verifying all containers are up).
- **11:30 - 12:30 (1.0h):** Attack 1 - Unauthorized Track Switching (API Bypasses).
- **12:30 - 13:30 (1.0h):** LUNCH BREAK
- **13:30 - 14:30 (1.0h):** Attack 2 - Heartbeat Failure & DoS (Fail-Safe triggers).
- **14:30 - 15:30 (1.0h):** Attack 3 & 4 - Sensor Spoofing & Alarm Flooding.
- **15:30 - 17:00 (1.5h):** Introduction to Wireshark in OT (Port 3000) & Packet Analysis.

### Day 2: Advanced Forensics & CTF (8 Hours)
**Focus:** SOC Analysis, Log Correlation, and the 10-Challenge Hackathon.
- **09:00 - 10:30 (1.5h):** ELK Stack / SOC Tools - Using Kibana and Zeek (AWS specific) or Wireshark PCAPs.
- **10:30 - 11:00 (0.5h):** CTF Registration & Rules (`http://localhost:8090`).
- **11:00 - 12:30 (1.5h):** CTF Competition - Phase 1 (Recon & Basic Exploits).
- **12:30 - 13:30 (1.0h):** LUNCH BREAK
- **13:30 - 16:30 (3.0h):** CTF Competition - Phase 2 (Advanced Forensics, Fuzzing, Memory Artifacts).
- **16:30 - 17:00 (0.5h):** Scoreboard Final Reveal, Winners, and Threat Mitigation Debrief.

---

## ⚔️ The Attacks (Day 1 Walkthroughs)

These are the exact commands students will run from their terminal, and exactly what will happen.

### Attack 1: Unauthorized Track Switching (API Bypass)
**Goal:** Prove that the Master PLC lacks authentication by forcing a track switch via API.
**What to Type:**
```bash
python scripts/modbus-attack.py
# Select Option 1
```
*(Alternatively, via curl)*:
```bash
curl -X POST http://localhost:8085/api/command -H "Content-Type: application/json" -d '{"segment_id": 2, "route": "ROUTE_B"}'
```
**What Happens:** 
1. The script bypasses the SCADA UI (Port 8081) and talks directly to the PLC (Port 8085).
2. Segment 2 switches to ROUTE_B.
3. The SCADA Dashboard's Audit Log catches this via correlation and flags it in **YELLOW** as `UNAUTHORIZED API CALL`.

### Attack 2: Safety Interlock Bypass (Sensor Spoofing)
**Goal:** Manipulate a field sensor to blind the Master PLC to a train's physical presence.
**What to Type:**
```bash
python scripts/modbus-attack.py
# Select Option 2
```
*(Alternatively, via curl)*:
```bash
curl -X POST http://localhost:8086/api/device/set -H "Content-Type: application/json" -d '{"device": "Occupancy Segment 1", "value": false}'
```
**What Happens:** 
1. The Slave PLC (`localhost:8086`) accepts the spoofed sensor data.
2. The Master PLC now believes the track is clear. 
**Discussion Point:** This is how Stuxnet worked—feeding false "safe" telemetry back to the operators while the centrifuges were spinning out of control.

### Attack 3: Alarm Flooding (Alert Fatigue)
**Goal:** Overwhelm the SCADA operator so they miss a real attack.
**What to Type:**
```bash
python scripts/modbus-attack.py
# Select Option 3
```
**What Happens:** 
1. The script sends 50 conflicting commands in 2 seconds.
2. Segment 3 flashes wildly between routes.
3. The Audit Log is buried in yellow alerts.

### Attack 4: Heartbeat Failure (DoS Simulation)
**Goal:** Simulate cutting the OT network cable to a Slave PLC.
**What to Type:**
```bash
docker stop railroad-slave-plc-1
```
**What Happens:** 
1. **Wait 15-20 seconds.** (The PLC tolerates 2 missed heartbeats to avoid false positives).
2. On the 3rd missed heartbeat, the Master PLC triggers a global `EMERGENCY_STOP`. All signals turn RED.
**Recovery:**
```bash
docker start railroad-slave-plc-1
# Wait 5 seconds, then click "Clear Faults" on the dashboard.
```

---

## 🚩 CTF Answer Key & Explanations (DO NOT SHARE)

The CTF server runs on `http://localhost:8090`. There are 10 challenges total. 

### 1. Network Reconnaissance (100 pts)
**Question:** Identify the IP address of the Master PLC on the OT network.
**Flag:** `172.25.0.10`
**Explanation:** Students open Wireshark (`localhost:3000`), filter by HTTP, and look at the source IP of `/api/status` responses.

### 2. Protocol Identification (100 pts)
**Question:** What port does the Master PLC listen on for Modbus TCP?
**Flag:** `502`
**Explanation:** Found in `docker-compose.yml` or by scanning with `nmap` from the pentest container.

### 3. Unauthorized Track Switch (200 pts)
**Question:** Switch Segment 1 to ROUTE_C directly. What is the value of the `requested_route` field in the response?
**Flag:** `ROUTE_C`
**Explanation:** They must construct the POST request manually or use the script and read the JSON response output.

### 4. Sensor Spoofing (250 pts)
**Question:** Spoof the occupancy sensor on Slave 1. Find the exact device name from the API response.
**Flag:** `Occupancy North`
**Explanation:** The UI says "Segment 1", but the actual internal device name returned by the Slave PLC's API is "Occupancy North".

### 5. Log Correlation (300 pts)
**Question:** After running the flood attack, how many total commands were recorded in `/api/status`?
**Flag:** `(Any number >= 50)`
**Explanation:** The CTF server uses a dynamic flag check here. If they run the flood script (which sends 50 packets), the `total_commands` counter will exceed 50.

### 6. Packet Capture Analysis (300 pts)
**Question:** Capture Attack 1. What is the exact JSON key used to specify the track segment?
**Flag:** `segment_id`
**Explanation:** Students must follow the TCP stream in Wireshark and read the raw HTTP POST body: `{"segment_id": 2, "route": "ROUTE_B"}`.

### 7. Emergency Recovery (200 pts)
**Question:** Perform a full recovery. What is the value of the `action` field from `/api/emergency/clear`?
**Flag:** `emergency_cleared`
**Explanation:** After restarting a stopped Slave PLC, they must either click the UI button while inspecting browser network traffic, or manually `curl` the endpoint to read the JSON response.

### 8. Safety Interlock Validation (350 pts)
**Question:** Try to switch Seg 2 to ROUTE_A while Seg 1 is on ROUTE_A. What is the exact 'reason' text returned?
**Flag:** `Conflicting routes at junction`
**Explanation:** The physical junction prevents two Express routes from colliding. The API returns this exact string when it rejects the command.

### 9. API Fuzzing (Insane - 400 pts)
**Question:** Fuzz the Master PLC by sending an invalid route (e.g., 'ROUTE_XYZ'). What is the exact error string?
**Flag:** `Invalid route: ROUTE_XYZ`
**Explanation:** Students must manually forge a bad request: `curl -X POST http://localhost:8085/api/command -d '{"segment_id": 1, "route": "ROUTE_XYZ"}' -H "Content-Type: application/json"`.

### 10. Deep Memory Forensics (Insane - 500 pts)
**Question:** A previous attacker left a hidden artifact in memory. Find the hidden flag string in the raw `/api/status` JSON.
**Flag:** `FLAG{modbus_master_pwned}`
**Explanation:** The SCADA Dashboard hides the `firmware_notes` field. Students *must* use `curl http://localhost:8085/api/status` or view the raw JSON in their browser to see the hidden debug flag inserted into the PLC memory.

---

## ☁️ AWS Full SOC Integration Notes

When deploying via `docker-compose-aws.yml`, the environment expands to 16 containers, introducing enterprise SOC tools.

1. **Zeek IDS (`localhost:5901` via VNC or logs in volume):** 
   - Deep Packet Inspection for Modbus traffic.
   - Look in `/zeek/logs/notice.log` for alerts triggered by the attacks.
2. **Elasticsearch / Kibana (`localhost:5601`):**
   - All syslog events from the PLCs are ingested here.
   - For Day 2, challenge students to build a Kibana dashboard showing the spike in `total_commands` during the Alarm Flooding attack.
3. **CTF Parity:**
   - The AWS compose file has been fully updated to include the `ctf-server` (Port 8090) and `wireshark` (Port 3000), meaning the CTF will run perfectly in the cloud environment just as it does locally.
