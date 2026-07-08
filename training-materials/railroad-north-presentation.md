---
marp: true
theme: default
class: lead
size: 16:9
style: |
  :root {
    --primary: #2563eb;
    --secondary: #0f172a;
    --accent: #38bdf8;
    --danger: #ef4444;
    --success: #22c55e;
    --text-main: #f8fafc;
    --text-muted: #cbd5e1;
  }
  section { 
    background-color: var(--secondary);
    color: var(--text-main);
    font-family: 'Inter', 'Segoe UI', sans-serif;
    padding: 40px 60px;
    font-size: 24px;
  }
  h1 { font-size: 2.8em; color: var(--accent); margin-bottom: 0.2em; font-weight: 800; }
  h2 { font-size: 1.6em; color: var(--text-main); border-bottom: 2px solid var(--primary); padding-bottom: 5px; margin-bottom: 20px; }
  h3 { color: var(--accent); font-size: 1.2em; margin-bottom: 10px; margin-top: 0; }
  p, li { font-size: 1.0em; line-height: 1.4; color: var(--text-muted); margin-bottom: 10px; }
  strong { color: #fff; font-weight: 600; }
  
  .card {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 15px 20px;
    margin: 10px 0;
    border-left: 4px solid var(--accent);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  }
  .card-danger { border-left-color: var(--danger); }
  .card-success { border-left-color: var(--success); }
  
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  
  table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.9em; background-color: transparent !important; }
  th { background-color: var(--primary) !important; color: white !important; padding: 12px; text-align: left; }
  td { padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: var(--text-main) !important; background-color: var(--secondary) !important; }
  tr:nth-child(even) td { background-color: #1e293b !important; }
  
  .highlight { color: var(--accent); font-weight: bold; }
  .alert { color: var(--danger); font-weight: bold; }
  
  code { background: #1e293b; color: #a78bfa; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; }
---

# Railroad North
## Applied OT & ICS Security Training
A Hands-On Workshop for Engineering & Cyber Security Students

---

## Workshop Overview

This is an **intensive hands-on workshop** that puts you inside a live OT environment.

<div class="grid">
  <div>
    <div class="card">
      <h3>Part 1: Guided Exploration</h3>
      <p>Understand OT/ICS fundamentals. Explore the SCADA dashboard. Execute supervised attack and defense scenarios against a live railway control system.</p>
    </div>
  </div>
  <div>
    <div class="card card-danger">
      <h3>Part 2: Capture The Flag</h3>
      <p>Apply everything you learned. Work in teams to solve 10 challenges across Reconnaissance, Exploitation, Forensics, and Defense categories using Wireshark and the lab tools.</p>
    </div>
  </div>
</div>

---

## What is Operational Technology (OT)?

Unlike traditional IT networks that manage **data**, OT networks manage **physical processes**. 

<div class="grid">
  <div>
    <h3>Traditional IT (Information Tech)</h3>
    <ul>
      <li><strong>Priority:</strong> Confidentiality & Data Protection</li>
      <li><strong>Impact:</strong> Data breaches, financial loss</li>
      <li><strong>Lifespan:</strong> Hardware replaced every 3-5 years</li>
      <li><strong>Patching:</strong> Regular, automated updates</li>
    </ul>
  </div>
  <div>
    <h3>OT (Operational Tech)</h3>
    <ul>
      <li><strong>Priority:</strong> <span class="highlight">Safety, Availability, Reliability</span></li>
      <li><strong>Impact:</strong> Physical damage, loss of human life</li>
      <li><strong>Lifespan:</strong> Equipment runs for 15-30 years</li>
      <li><strong>Patching:</strong> Extremely rare; requires system downtime</li>
    </ul>
  </div>
</div>

---

## Introduction to the Railroad North Lab

This laboratory simulates a **Critical Infrastructure Railway System**. It is designed to safely teach you how these systems work and how they can be compromised.

<div class="card">
  <strong>The Core Mission</strong>
  You will step into the shoes of both an attacker and a defender. You will learn how to read industrial protocols, bypass physical safety interlocks, and detect these attacks using network forensics and log correlation.
</div>

---

## Lab Architecture & Components

Our environment runs on an **AWS cloud instance** with 8+ Docker containers across 3 segmented networks:

| Container | Role | Access URL |
|---|---|---|
| **SCADA Dashboard** | Operator Interface | `http://13.206.102.61:8081` |
| **Master PLC** | Central Coordinator | `http://13.206.102.61:8085` |
| **Syslog Collector** | Log Aggregation | Internal only (OT network) |
| **Wireshark** | Packet Analysis | `https://13.206.102.61:3001` |
| **CTF Server** | Challenge Scoring | `http://13.206.102.61:8090` |

> ⚠️ Wireshark uses HTTPS. Your browser will show a security warning — click **Advanced → Proceed** to continue.

---

## The Purdue Enterprise Reference Architecture

Our lab is segmented strictly according to the industry-standard Purdue Model.

<table>
  <tr>
    <th>Zone</th>
    <th>Level</th>
    <th>Components in our Lab</th>
  </tr>
  <tr>
    <td><strong>IT / Enterprise</strong></td>
    <td>Level 4</td>
    <td>Your laptop (the attacker's workstation)</td>
  </tr>
  <tr>
    <td><strong>DMZ (Demilitarized)</strong></td>
    <td>Level 3.5</td>
    <td>SCADA Web Dashboard, CTF Scoreboard (172.27.x.x)</td>
  </tr>
  <tr>
    <td><strong>OT / Control</strong></td>
    <td>Level 1-3</td>
    <td>Master PLC, Syslog Collector, Wireshark (172.25.x.x)</td>
  </tr>
  <tr>
    <td><strong>Field Devices</strong></td>
    <td>Level 0</td>
    <td>Slave PLCs controlling Switches, Barriers, and Signals</td>
  </tr>
</table>

---

## Deep Dive: How the Railway is Controlled

To secure the railway, you must first understand how it operates.

<div class="grid">
  <div>
    <div class="card">
      <h3>1. The Master PLC (The Brain)</h3>
      <p>The central coordinator. It stores the "global truth" of the railway. It continuously polls the Slave PLCs every 5 seconds via a <strong>Heartbeat</strong> and enforces safety interlock rules before allowing any track switch.</p>
    </div>
  </div>
  <div>
    <div class="card">
      <h3>2. The Slave PLCs (The Muscle)</h3>
      <p>Located in the North, Central, and South segments. These directly control physical track switches, signals, and barriers. They report sensor data to the Master and execute its commands.</p>
    </div>
  </div>
</div>

---

## API Communication: The Attack Surface

Our PLCs communicate using **REST APIs over HTTP** (simulating the insecurity of real-world Modbus TCP).

<div class="card card-danger">
  <strong>The Security Flaw:</strong> The API endpoints have zero authentication. If you can reach the network port, the PLC will execute your command without verifying who sent it.
</div>

**Key API Endpoints You Will Target:**
- `GET /api/status` - Read the full system state (reconnaissance)
- `POST /api/command` - Switch a track route (exploitation)
- `POST /api/device/set` - Manipulate field sensors (sensor spoofing)
- `POST /api/emergency` - Trigger an emergency stop

---

## Built-In Safety Interlocks (Defensive Logic)

To prevent catastrophic train derailments, the Master PLC has hard-coded safety logic:

1. **Route Conflict Prevention:** The Master PLC checks if two connecting segments are requesting conflicting routes at a junction. If they conflict, the command is <span class="alert">rejected</span>.
2. **Track Occupancy Lock:** A track switch will not operate if the occupancy sensor detects a train currently on that segment.
3. **Barrier Enforcement:** Routes cannot be cleared unless physical crossing barriers are confirmed to be lowered and locked.
4. **Heartbeat Monitoring:** If the Master PLC loses connection to a Slave PLC (3 missed heartbeats), it triggers a global **EMERGENCY STOP**.

---

# PART 1
## Guided Attack & Defense Scenarios

---

## Scenario 1: Unauthorized Track Switching

**Concept:** An adversary bypasses the SCADA dashboard and sends a direct API command to switch a track route.

<div class="grid">
  <div>
    <div class="card card-danger">
      <h3>The Attack</h3>
      <p>Run <code>python scripts/modbus-attack.py</code> and select <strong>Option 1</strong>. This sends a direct POST request to the Master PLC, bypassing the SCADA operator entirely.</p>
    </div>
  </div>
  <div>
    <div class="card card-success">
      <h3>The Defense</h3>
      <p>Watch the SCADA Dashboard. The System Audit Log will show the command in <strong>yellow</strong> (UNAUTHORIZED API CALL) instead of green (legitimate operator command). This is <strong>Log Correlation</strong> in action.</p>
    </div>
  </div>
</div>

---

## Scenario 2: Heartbeat Failure (DoS Attack)

**Concept:** A segment of the railway loses connectivity due to a Denial of Service attack or a physical network cut.

<div class="grid">
  <div>
    <div class="card card-danger">
      <h3>The Attack</h3>
      <p>Run <code>docker stop railroad-slave-plc-1</code> in your terminal. This simulates cutting the network cable to the North segment. Wait 15-20 seconds.</p>
    </div>
  </div>
  <div>
    <div class="card card-success">
      <h3>The Defense</h3>
      <p>Watch the dashboard enter <strong>EMERGENCY STOP</strong> automatically. The Master PLC detected 3 missed heartbeats and triggered the fail-safe. The system "fails closed" for physical safety.</p>
    </div>
  </div>
</div>

**Recovery:** `docker start railroad-slave-plc-1`, wait 5 seconds, then click **Clear Faults** on the SCADA dashboard.

---

## Scenario 3: SCADA Alarm Flooding

**Concept:** The attacker overwhelms the SCADA operator by flooding the system with rapid, conflicting commands.

<div class="grid">
  <div>
    <div class="card card-danger">
      <h3>The Attack</h3>
      <p>Run <code>python scripts/modbus-attack.py</code> and select <strong>Option 3</strong>. This fires 50 commands in 5 seconds, rapidly toggling a track switch back and forth.</p>
    </div>
  </div>
  <div>
    <div class="card card-success">
      <h3>The Defense</h3>
      <p>The Audit Log is overwhelmed with yellow warnings. In a real SOC, this is called <strong>Alert Fatigue</strong>. Defenders must implement rate limiting and anomaly detection to filter the noise from genuine threats.</p>
    </div>
  </div>
</div>

---

## Scenario 4: Safety Interlock Validation

**Concept:** Verify that the safety interlocks actually prevent dangerous operations even under attack.

<div class="grid">
  <div>
    <div class="card card-danger">
      <h3>The Test</h3>
      <p>Set Segment 1 to ROUTE_A, then attempt to set Segment 2 to ROUTE_A. The Master PLC should <strong>reject</strong> this because the routes conflict at the junction. The Audit Log will show a <strong>red REJECTED</strong> entry with the reason.</p>
    </div>
  </div>
  <div>
    <div class="card card-success">
      <h3>The Takeaway</h3>
      <p>Even if an attacker gains full API access, the <strong>hard-coded safety logic</strong> in the PLC firmware provides the last line of defense. This is why OT security uses a <strong>defense-in-depth</strong> strategy.</p>
    </div>
  </div>
</div>

---

## Using Wireshark for Network Forensics

Open **Wireshark** at `https://13.206.102.61:3001` in your browser. Click **Advanced → Proceed** on the security warning.

<div class="card">
  <h3>What to Look For</h3>
  <ul>
    <li><strong>HTTP POST requests</strong> to <code>/api/command</code> -- These are route switch commands</li>
    <li><strong>Rapid request bursts</strong> -- Indicates a flood/DoS attack</li>
    <li><strong>Unauthorized source IPs</strong> -- Commands not from the SCADA server (172.27.0.20)</li>
    <li><strong>Heartbeat gaps</strong> -- Missing periodic GET requests from Slave PLCs</li>
  </ul>
</div>

Practice capturing traffic while a partner runs the attack scripts. You will need these skills for the CTF.

---

# PART 2
## Capture The Flag Challenge

---

## CTF Rules & Setup

<div class="grid">
  <div>
    <div class="card">
      <h3>How it Works</h3>
      <ul>
        <li>Open the <strong>CTF Scoreboard</strong> at <code>http://13.206.102.61:8090</code></li>
        <li>Register your team name</li>
        <li>Solve challenges and submit flags to earn points</li>
        <li>10 challenges across 4 categories</li>
        <li>Total possible score: <strong>2,400 points</strong></li>
      </ul>
    </div>
  </div>
  <div>
    <div class="card card-danger">
      <h3>Categories</h3>
      <ul>
        <li><strong>Reconnaissance (200 pts):</strong> Map the OT network</li>
        <li><strong>Exploitation (850 pts):</strong> Execute attacks and fuzz APIs</li>
        <li><strong>Forensics (1,100 pts):</strong> Analyze PCAPs and memory</li>
        <li><strong>Defense (550 pts):</strong> Recover and validate</li>
      </ul>
    </div>
  </div>
</div>

---

## CTF Tools Available

You have access to these tools during the CTF:

| Tool | Access | Purpose |
|---|---|---|
| **SCADA Dashboard** | `http://13.206.102.61:8081` | Monitor the system state in real time |
| **Wireshark** | `https://13.206.102.61:3001` | Capture and analyze network traffic |
| **Attack Script** | `python scripts/modbus-attack.py` | Pre-built attack vectors |
| **curl / browser** | Your terminal | Craft custom API requests |
| **Master PLC API** | `http://13.206.102.61:8085/api/status` | Directly query system state |

---

## CTF Challenge Preview

| # | Challenge | Category | Points | Difficulty |
|---|---|---|---|---|
| 1 | Network Reconnaissance | Recon | 100 | Easy |
| 2 | Protocol Identification | Recon | 100 | Easy |
| 3 | Unauthorized Track Switch | Exploit | 200 | Medium |
| 4 | Sensor Spoofing | Exploit | 250 | Medium |
| 5 | Log Correlation | Forensics | 300 | Hard |
| 6 | Packet Capture Analysis | Forensics | 300 | Hard |
| 7 | Emergency Recovery | Defense | 200 | Medium |
| 8 | Safety Interlock Validation | Defense | 350 | Hard |
| 9 | API Fuzzing | Exploit | 400 | Insane |
| 10 | Deep Memory Forensics | Forensics | 500 | Insane |

**Hints are available but cost -50 points each!**

---

## Lab Access Summary

| What | Where |
|---|---|
| SCADA Dashboard | `http://13.206.102.61:8081` |
| CTF Scoreboard | `http://13.206.102.61:8090` |
| Wireshark | `https://13.206.102.61:3001` (click Advanced → Proceed) |
| Master PLC API | `http://13.206.102.61:8085/api/status` |
| Attack Script | `python scripts/modbus-attack.py` |

---

# Questions & Lab Kickoff

### Open your browser and navigate to the SCADA Dashboard to begin.
### `http://13.206.102.61:8081`
*The instructor will walk you through the first scenario.*
