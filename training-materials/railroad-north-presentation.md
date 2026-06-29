---
marp: true
theme: default
class: lead
backgroundColor: #1a1a2e
color: #e2e8f0
style: |
  h1, h2, h3, h4, h5, h6 { color: #38bdf8; }
  a { color: #f472b6; }
  section { font-family: 'Inter', sans-serif; }
  .box { padding: 20px; background: rgba(255,255,255,0.05); border-radius: 10px; border-left: 4px solid #38bdf8; margin-top: 20px;}
  code { background: #0f172a; color: #a78bfa; border-radius: 4px; padding: 2px 5px;}
---

# Railroad North
## OT Security Training Lab
Lab Overview and Scenarios

---

## Lab Objectives

This lab is designed to give you hands-on experience with industrial control systems and how to defend them. 

By the end of this session, you should be able to:
1. Understand the basic architecture of a Master-Slave PLC setup using Modbus TCP.
2. Monitor and analyze OT network traffic.
3. Use tools like Zeek and ELK to detect abnormal behavior.
4. Respond to simulated attacks in a controlled environment.

---

## Network Architecture

We are using a standard three-tier model for this setup:

- **IT Network (172.26.0.0/16)**: Used for engineering workstations and basic file transfers.
- **DMZ Network (172.27.0.0/16)**: Hosts the SCADA Web UI and syslog aggregators.
- **OT Network (172.25.0.0/16)**: The core network containing the Master PLC, Slave PLCs, Modbus traffic, and the monitoring stack.

---

## Core Components

<div class="box">
<strong>Master PLC</strong>
Acts as the central controller. It enforces safety rules, validates routes, and continuously polls the Slave PLCs.
</div>

<div class="box">
<strong>Slave PLCs (North, Central, South)</strong>
These control the actual track segments. They operate the switches, signals, and barriers, and report back to the Master.
</div>

<div class="box">
<strong>SCADA Dashboard</strong>
The web interface used by operators to monitor track status and send routing commands.
</div>

---

## Safety Mechanisms

The system has physical safety logic built in to prevent accidents:

1. **Track Occupancy Lock**: A track switch will not operate if a train is currently on that segment.
2. **Barrier Enforcement**: Routes cannot be changed if the physical barriers are not in the correct lowered state.
3. **Heartbeat Monitoring**: The Master polls the Slaves every 5 seconds. If communication fails, the system safely halts and enters a FAULT state.

---

## Monitoring Setup

To monitor the OT network, we have integrated a basic SOC stack:

- **Syslog Collector**: Gathers logs from all components.
- **Zeek IDS**: Inspects network traffic on port 502. We added custom signatures to catch Modbus anomalies.
- **Elasticsearch & Logstash**: Parses the logs and indexes them.
- **Kibana**: Provides dashboards to visualize the data and alerts.

---

## Training Scenarios

We will go through 4 specific attack scenarios today.

---

### Scenario 1: Unauthorized Track Switching

**Goal**: Detect route change commands sent from an unauthorized IP.
**Attack**: An attacker bypasses the SCADA interface and sends a direct Modbus write command to the Master PLC.
**Defense**: 
- Find the unauthorized IP in the Kibana logs.
- Check the Zeek notice.log for any triggered signatures.
- Discuss how firewall rules could prevent this.

---

### Scenario 2: PLC Heartbeat Failure

**Goal**: Handle a Denial of Service (DoS) situation against a segment controller.
**Attack**: One of the Slave PLCs is taken offline to simulate a failure or isolation.
**Defense**:
- Watch the Master PLC transition into the FAULT state.
- Locate the missing heartbeat logs in ELK.
- Walk through the standard E-STOP (Emergency Stop) recovery procedure.

---

### Scenario 3: Safety Interlock Bypass

**Goal**: See what happens when sensor data is manipulated.
**Attack**: An attacker forces the Occupancy Sensor state on a Slave PLC to change while a train is present, attempting to switch the track.
**Defense**:
- Analyze the logs to find conflicting sensor states.
- Discuss how to write custom Zeek rules to alert on impossible state changes.

---

### Scenario 4: Modbus Protocol Manipulation

**Goal**: Detect reconnaissance and malformed Modbus traffic.
**Attack**: We will run a script that performs Modbus scanning and function-code fuzzing against the PLCs.
**Defense**:
- Identify the scanning patterns in the network traffic.
- Detect the invalid function codes being dropped by the PLCs.

---

## Deployment Details

The lab runs on Docker. Depending on resources, we use two configurations:

- **Local Setup**: A lightweight 6-container setup (PLCs + SCADA) that runs well on standard laptops.
- **Cloud Setup**: The full 17-container setup, which includes the entire ELK stack and Zeek IDS, hosted on AWS.

---

# Questions?

Let's get started with Scenario 1.
