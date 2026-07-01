# Railroad North - OT Security Training Lab

A Operational Technology (OT) and ICS security training lab that simulates a Critical Infrastructure Railway System using a Master/Slave PLC architecture. Students learn OT security fundamentals through guided attack and defense scenarios, then apply their skills in a Capture The Flag competition.

## Prerequisites

- Docker Desktop installed and running
- At least 8GB RAM available

## Quick Start

```bash
# start the containers
docker-compose up -d

# verify everythin is runnin (8 containers)
docker ps

# and stop at end 
docker-compose down
```

## Accessing the Lab

Once the containers are running, open these URLs in your browser:

| Service | URL | Purpose |
|---|---|---|
| **SCADA Dashboard** | [http://localhost:8081](http://localhost:8081) | Main operator control interface |
| **CTF Scoreboard** | [http://localhost:8090](http://localhost:8090) | Day 2 challenge submission and scoring |
| **Wireshark** | [http://localhost:3000](http://localhost:3000) | Web-based packet capture and analysis |
| **Master PLC API** | [http://localhost:8085/api/status](http://localhost:8085/api/status) | Raw PLC status (JSON) |

## Architecture

The lab follows the Purdue Enterprise Reference Architecture across 3 segmented networks:

```
IT Network (172.26.x.x)      your lap (the attacker)
        |
   [ DMZ (172.27.x.x) ]      SCADA Dashboard, CTF Server
        |
  OT Network (172.25.x.x)    Master PLC, Slave PLCs, Wireshark, Syslog
```

### Containers

| # | Container | Role | Port |
|---|---|---|---|
| 1 | `railroad-scada` | SCADA Operator Dashboard | 8081 |
| 2 | `railroad-master-plc` | Central PLC Coordinator | 8085 |
| 3 | `railroad-slave-plc-1` | North Segment Controller | 8086 |
| 4 | `railroad-slave-plc-2` | Central Segment Controller | 8087 |
| 5 | `railroad-slave-plc-3` | South Segment Controller | 8088 |
| 6 | `railroad-collector` | Syslog Aggregation | 5140 |
| 7 | `railroad-wireshark` | Web-based Wireshark | 3000 |
| 8 | `railroad-ctf` | CTF Flag Server | 8090 |

## Structure

Students are walked through 4 supervised attack and defense scenarios:

1. **Unauthorized Track Switching** - Bypass the SCADA dashboard via direct API calls
2. **Heartbeat Failure (DoS)** - Simulate a network cut with `docker stop`; observe the E-STOP safety interlock
3. **SCADA Alarm Flooding** - Overwhelm the operator with 50 rapid commands
4. **Safety Interlock Validation** - Test that hard-coded PLC logic prevents dangerous operations

#### Running the Attack Script

```bash
python scripts/modbus-attack.py
```

This presents a menu with 3 attack options. No additional Python packages are required (uses only standard libraries).

#### Simulating a DoS Attack

```bash
docker stop railroad-slave-plc-1

# wait 15 to 20 secs for the E-STOP to trigger on the dashboard

docker start railroad-slave-plc-1
# then click "Clear Faults" on the Dashboard
```

### Capture The Flag 


| Category | Challenges | Points |
|---|---|---|
| Reconnaissance | Network mapping, protocol ID | 200 |
| Exploitation | Track switching, sensor spoofing | 450 |
| Forensics | Log correlation, packet analysis | 600 |
| Defense | Emergency recovery, interlock validation | 550 |

Open the CTF Scoreboard at [http://localhost:8090](http://localhost:8090), register a team name, and start solving.

## Presentation Slides

A complete slide deck is included in `training-materials/railroad-north-presentation.md`. View and export using the [Marp for VS Code](https://marketplace.visualstudio.com/items?itemName=marp-team.marp-vscode) extension.

## Troubleshooting

| Issue | Fix |
|---|---|
| Dashboard not loading | Run `docker restart railroad-scada` and wait 10 seconds |
| Attack script fails | Ensure containers are running with `docker ps` |
| Clear Faults not working | Make sure all Slave PLCs are started first, then click the button |
| Wireshark not loading | The image is large (~500MB); wait for the pull to complete |
| E-STOP won't clear | Run `docker start` on any stopped slaves, wait 10s, then Clear Faults |
