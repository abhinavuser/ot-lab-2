# Scenario 1: Unauthorized Track Switching

## Objective
Demonstrate how an attacker with network access can bypass the SCADA operator interface and directly command the Master PLC to switch a track route.

## Background
In real OT environments, SCADA operators are the only authorized personnel who should issue control commands. However, because the Master PLC's API has no authentication, anyone on the network can send commands directly.

## Attack Steps

1. Open your terminal and navigate to the lab directory.
2. Run the attack script:
   ```bash
   python scripts/modbus-attack.py
   ```
3. Select **Option 1: Unauthorized Track Switching**.
4. The script sends a POST request directly to `http://localhost:8085/api/command` with:
   ```json
   {"segment_id": 2, "route": "ROUTE_B"}
   ```
5. Observe the SCADA Dashboard at `http://localhost:8081`.

## What to Observe

- **On the Dashboard:** Segment 2 (Central Junction) will switch from its current route to ROUTE_B. The active route button will light up in yellow.
- **In the Audit Log:** The entry will appear in **yellow** labeled `UNAUTHORIZED API CALL` instead of the green `COMMAND ACCEPTED` that appears when the operator clicks a button.

## Defense Discussion

- Why did this work? The API has no authentication mechanism.
- How would you fix it? Implement API key authentication, IP whitelisting, or mutual TLS.
- What detected it? The SCADA dashboard's log correlation engine compared its own command history against the Master PLC's logs and identified the mismatch.

## Recovery

Click "Route A (Express)" on Segment 2 in the SCADA Dashboard to restore the original route.
