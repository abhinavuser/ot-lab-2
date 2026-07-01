# Scenario 2: Heartbeat Failure (Denial of Service)

## Objective
Demonstrate what happens when a Slave PLC loses connectivity to the Master PLC, simulating a Denial of Service (DoS) attack or a physical network cable being severed.

## Background
The Master PLC polls each Slave PLC every 5 seconds with a "heartbeat" check. If a Slave misses 3 consecutive heartbeats (approximately 15-20 seconds), the Master PLC concludes that it has lost situational awareness over that track segment and triggers a global Emergency Stop (E-STOP) to prevent trains from entering an unmonitored section.

## Attack Steps

1. Open the SCADA Dashboard at `http://localhost:8081` and confirm all segments show `State: IDLE`.
2. In your terminal, stop the North Segment Slave PLC:
   ```bash
   docker stop railroad-slave-plc-1
   ```
3. Wait 15-20 seconds while watching the dashboard.
4. The Master PLC will detect 3 missed heartbeats and trigger EMERGENCY STOP.

## What to Observe

- **On the Dashboard:** All 3 segments will switch to `State: EMERGENCY_STOP` with `Signal: RED`. The system fails globally, not just locally, because a blind spot anywhere on the network is a danger to the entire railway.
- **In the PLC Logs:** Run `docker logs railroad-master-plc --tail 20` to see the heartbeat failure warnings and the E-STOP trigger.

## Defense Discussion

- This is a **fail-safe mechanism**: the system "fails closed" to protect human life.
- In real railways, a heartbeat failure triggers an automatic brake application on all trains in the affected zone.
- This is an example of **defense-in-depth**: even if the attacker disrupts connectivity, the safety logic prevents a catastrophe.

## Recovery

```bash
# 1. Restart the Slave PLC
docker start railroad-slave-plc-1

# 2. Wait 10 seconds for the heartbeat to reconnect

# 3. Click "Clear Faults" on the SCADA Dashboard
```

**Important:** If you click "Clear Faults" before the Slave is back online, the E-STOP will immediately trigger again because the heartbeat is still missing.
