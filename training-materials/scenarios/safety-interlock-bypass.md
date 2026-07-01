# Scenario 3: Safety Interlock Bypass (Sensor Spoofing)

## Objective
Demonstrate how an attacker can manipulate sensor data at the field device level to trick the Master PLC's safety logic into allowing a dangerous operation.

## Background
The Master PLC relies on occupancy sensor data from the Slave PLCs to determine whether a train is on the track. If the sensor reports "occupied," the PLC will refuse to switch the track. But what if an attacker spoofs the sensor to report "clear" when a train is actually present?

## Attack Steps

1. Open the SCADA Dashboard and confirm Segment 1 shows `Occupied: NO`.
2. Run the attack script:
   ```bash
   python scripts/modbus-attack.py
   ```
3. Select **Option 2: Safety Interlock Bypass / Sensor Spoofing**.
4. The script sends a POST request to Slave PLC 1's `/api/device/set` endpoint:
   ```json
   {"device": "Occupancy Segment 1", "value": false}
   ```

## What to Observe

- The Slave PLC accepts the command and changes the sensor state.
- The Master PLC now believes the track is clear, even if a train were physically present.
- This demonstrates the **most dangerous class of OT attack**: manipulating the physical feedback loop that safety systems rely on.

## Defense Discussion

- Why is this dangerous? The safety interlock is only as trustworthy as the sensor data it receives. If the sensor is spoofed, the interlock is blind.
- In real systems, physical sensors use redundancy (multiple independent sensors) to detect spoofing.
- Network segmentation should prevent unauthorized devices from reaching field-level PLCs.

## Recovery

The system will continue operating normally since we spoofed the sensor to "clear" (a safe state). No recovery action needed for this demo.

## Advanced Exercise

Try spoofing the sensor to `true` (occupied) and then attempt to switch the track via the SCADA dashboard. You should see the interlock reject the command. This proves the safety logic works correctly when sensor data is honest.
