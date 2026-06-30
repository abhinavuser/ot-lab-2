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
Presented to Engineering & Cyber Security Students

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
  You will step into the shoes of both an attacker and a defender. You will learn how to read industrial protocols, bypass physical safety interlocks, and finally, how to detect and stop these attacks using modern SOC (Security Operations Center) tools.
</div>

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
    <td>Engineering Workstations, Corporate File Transfers (Subnet: 172.26.x.x)</td>
  </tr>
  <tr>
    <td><strong>DMZ (Demilitarized)</strong></td>
    <td>Level 3.5</td>
    <td>SCADA Web Dashboard, Syslog Aggregator, Secure Proxies (Subnet: 172.27.x.x)</td>
  </tr>
  <tr>
    <td><strong>OT / Control</strong></td>
    <td>Level 1-3</td>
    <td>Master PLC, Zeek IDS, ELK Stack (Subnet: 172.25.x.x)</td>
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
      <p>The Master Programmable Logic Controller acts as the central coordinator. It stores the "global truth" of the railway. It continuously polls the Slave PLCs every 5 seconds (Heartbeat) and enforces safety rules.</p>
    </div>
  </div>
  <div>
    <div class="card">
      <h3>2. The Slave PLCs (The Muscle)</h3>
      <p>Located in the North, Central, and South segments. These directly open/close physical track switches and lower barriers. They blindly follow the Master's orders.</p>
    </div>
  </div>
</div>

---

## Modbus TCP: The Language of Industry

Our PLCs communicate using **Modbus TCP**, a protocol from 1979 that is still used globally today.

<div class="card card-danger">
  <strong>The Security Flaw:</strong> Modbus TCP has zero encryption and zero authentication. If you can reach the network port (502), the PLC will execute your command.
</div>

**Key Modbus Functions You Will See:**
- `Function 0x03 (Read Holding Registers)`: Used by the Master to check sensor states.
- `Function 0x06 (Write Single Register)`: Used by the SCADA UI to change a track route.
- `Function 0x0F (Write Multiple Coils)`: Used to trigger emergency stops.

---

## Built-In Safety Interlocks (Defensive Logic)

To prevent catastrophic train derailments, our Master PLC has hard-coded safety logic:

1. **Track Occupancy Lock:** A track switch <span class="alert">will not operate</span> if the occupancy sensor detects a train currently on that specific segment.
2. **Barrier Enforcement:** Train routes cannot be cleared unless physical crossing barriers are confirmed to be lowered and locked.
3. **Heartbeat Monitoring:** If the Master PLC loses connection to a Slave PLC, it triggers a global `FAULT` state, halting all trains.

---

## The Defender's Toolkit (SOC Stack)

Because Modbus is insecure by design, we must rely on **network monitoring** to secure the OT environment.

<div class="grid">
  <div>
    <ul>
      <li><strong>Zeek IDS:</strong> An Intrusion Detection System. It performs Deep Packet Inspection (DPI) on port 502 to alert us to malformed Modbus traffic or unauthorized writes.</li>
      <li><strong>Syslog Collector:</strong> Aggregates every command and error from the PLCs into a central server.</li>
    </ul>
  </div>
  <div>
    <ul>
      <li><strong>Elasticsearch & Logstash:</strong> Ingests millions of log events and indexes them for rapid searching.</li>
      <li><strong>Kibana:</strong> Our visual dashboard. Used by analysts to spot anomalies (like a sudden spike in Modbus traffic).</li>
    </ul>
  </div>
</div>

---

## Training Scenarios

You will now execute and defend against four distinct cyber-physical attacks.

---

### Scenario 1: Unauthorized Track Switching

**The Concept:** An adversary gains access to the OT network and attempts to switch a track route, bypassing the SCADA operator dashboard.

<div class="grid">
  <div>
    <div class="card card-danger">
      <h3>The Attack</h3>
      <p>The student will use a script to send a direct Modbus <code>Write Register (0x06)</code> command to the Master PLC from an unauthorized IP address.</p>
    </div>
  </div>
  <div>
    <div class="card card-success">
      <h3>The Defense</h3>
      <p>Identify the rogue IP address using the Kibana dashboard. Review the Zeek <code>notice.log</code> to see exactly which register was modified, and propose firewall segmentation rules.</p>
    </div>
  </div>
</div>

---

### Scenario 2: PLC Heartbeat Failure (DoS)

**The Concept:** A segment of the railway loses connectivity due to a cyber-attack (DoS) or a physical network cut.

<div class="grid">
  <div>
    <div class="card card-danger">
      <h3>The Attack</h3>
      <p>We will intentionally isolate a Slave PLC, severing its connection to the Master controller.</p>
    </div>
  </div>
  <div>
    <div class="card card-success">
      <h3>The Defense</h3>
      <p>Watch the Master PLC automatically trigger the safety interlock and enter a <code>FAULT</code> state. Students will use the logs to determine the exact timestamp of the network loss and execute the standard E-STOP recovery procedure.</p>
    </div>
  </div>
</div>

---

### Scenario 3: Safety Interlock Bypass

**The Concept:** What happens if an attacker manipulates the sensor data that the safety logic relies on?

<div class="grid">
  <div>
    <div class="card card-danger">
      <h3>The Attack</h3>
      <p>The attacker forces the "Occupancy Sensor" value on a Slave PLC to <code>False</code> (Clear), tricking the Master PLC into allowing a track switch while a train is actually present.</p>
    </div>
  </div>
  <div>
    <div class="card card-success">
      <h3>The Defense</h3>
      <p>This is the most dangerous scenario. Students will analyze the logs for impossible physics (e.g., a track clearing in 0.1 seconds) and learn to write custom Zeek rules to alert on rapid sensor-state toggling.</p>
    </div>
  </div>
</div>

---

### Scenario 4: Modbus Protocol Fuzzing

**The Concept:** Attackers often map out a network before striking. We must detect them during the reconnaissance phase.

<div class="grid">
  <div>
    <div class="card card-danger">
      <h3>The Attack</h3>
      <p>Students will use the <code>modbus-attack.py</code> toolkit to rapidly scan the PLC and send malformed function codes to map out the memory registers.</p>
    </div>
  </div>
  <div>
    <div class="card card-success">
      <h3>The Defense</h3>
      <p>Identify the automated scanning patterns in the network traffic. Detect the specific <code>Illegal Function</code> exception codes being dropped and logged by the PLCs.</p>
    </div>
  </div>
</div>

---

## Lab Execution & Deliverables

Your task is to work through these scenarios on your local lab instance. 

1. **Access the Dashboard:** Go to <code>http://localhost:8080</code> to view the SCADA system.
2. **Review the Logs:** Analyze the output of the Master PLC and the Syslog collector.
3. **Document Findings:** For each scenario, document the Attack Vector, the resulting System Impact, and the Defensive Mitigation.

---

# Questions & Lab Kickoff

### Please navigate to your local lab instance to begin.
*The TA will be walking around to assist with networking or Docker issues.*
