# Railroad North - Student Lab Guide

Welcome to the Railroad North OT Security Lab! In this lab, you will act as both a Red Team attacker and a Blue Team defender against a critical infrastructure railway system.

## Your Workstation

You have access to the following interfaces:
1. **SCADA Dashboard (`http://localhost:8081`)**: This is the operator interface. You can view the status of the trains, switches, and safety barriers here.
2. **The Terminal**: You will use your command line to launch attacks and view system logs.

---

## The Missions

### Scenario 1: Modbus Protocol Fuzzing
Before attacking, hackers scan the network. 
1. Open your terminal and run the attack script:
   ```bash
   python scripts/modbus-attack.py --target 172.25.0.10 --fuzz
   ```
2. **Defender Task**: Open a second terminal and monitor the Master PLC logs to see what the attacker is doing:
   ```bash
   docker logs -f railroad-master-plc
   ```
   *Can you see the illegal function codes being rejected by the PLC?*

### Scenario 2: Heartbeat Failure (DoS)
What happens if a physical network cable is cut or a DoS attack takes a PLC offline?
1. In your terminal, "kill" one of the field devices:
   ```bash
   docker stop railroad-slave-plc-1
   ```
2. **Defender Task**: Look at the SCADA Dashboard. Watch what happens when the Master PLC fails to receive the 5-second heartbeat. How does the safety interlock protect the trains?

### Scenario 3: Unauthorized Track Switching
Let's try to bypass the SCADA dashboard entirely and talk directly to the PLC using Modbus TCP.
1. Run the attack script to force a route change on Segment 2:
   ```bash
   python scripts/modbus-attack.py --target 172.25.2.10 --write-register 40001 2
   ```
2. **Defender Task**: Check the SCADA dashboard. Did the route change? Why or why not? Look at the logs to find the IP address of the attacker.

## Conclusion
Once you have completed the scenarios, you should understand that Modbus TCP has no built-in security, and why physical safety interlocks (like heartbeats and occupancy sensors) are the only thing preventing catastrophic accidents in the physical world.
