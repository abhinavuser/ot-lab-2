# Scenario 4: SCADA Alarm Flooding (Alert Fatigue Attack)

## Objective
Demonstrate how an attacker can overwhelm a SCADA operator by flooding the system with rapid, conflicting commands, causing "alert fatigue" and potentially masking a real attack.

## Background
In a Security Operations Center (SOC), analysts monitor dashboards for anomalies. If an attacker can generate hundreds of false alarms in seconds, the real attack gets buried in noise. This is a well-documented tactic used in real-world OT attacks, including the 2015 Ukraine power grid attack.

## Attack Steps

1. Open the SCADA Dashboard at `http://localhost:8081` and watch the System Audit Log panel.
2. Run the attack script:
   ```bash
   python scripts/modbus-attack.py
   ```
3. Select **Option 3: SCADA Alarm Flooding / DoS**.
4. The script fires 50 commands in rapid succession, toggling Segment 3 between ROUTE_A and ROUTE_B every 100 milliseconds.

## What to Observe

- **In the Audit Log:** A massive wall of yellow `UNAUTHORIZED API CALL` entries floods the log panel. The legitimate entries become impossible to find.
- **On the Dashboard:** Segment 3 (South Yard) rapidly flashes between ROUTE_A and ROUTE_B as the track switch is toggled back and forth.
- **Commands Issued Counter:** The counter in the status bar will spike dramatically.

## Defense Discussion

- **Alert Fatigue** is one of the top challenges for SOC analysts. When there are too many alerts, critical ones get missed.
- Defenses include: rate limiting API requests, implementing anomaly detection (flag sudden spikes in command frequency), and using SIEM correlation rules.
- In our lab, the Wireshark capture will show a clear pattern of rapid HTTP POST requests from the same source, which is easy to detect with proper tooling.

## Recovery

Click any route button on Segment 3 in the SCADA Dashboard to set it to a stable state.
