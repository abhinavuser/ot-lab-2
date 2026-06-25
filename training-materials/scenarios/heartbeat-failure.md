# Scenario 2: PLC Heartbeat Failure

## Objective
Detect loss of slave PLC communication and verify emergency response.

## Difficulty: Easy | Duration: 15 minutes

## Steps

```bash
# 1. Stop a slave PLC to simulate failure
docker stop railroad-slave-plc-2

# 2. Monitor master PLC logs for heartbeat failure
docker logs -f railroad-master-plc

# 3. Check SCADA UI - Segment 2 should show FAULT
# Open http://localhost:8080

# 4. Check collector logs
docker logs railroad-collector | grep HEARTBEAT

# 5. Restart the slave to recover
docker start railroad-slave-plc-2
```

## Expected Behavior
- Master PLC detects missed heartbeats within 15-20 seconds
- Segment 2 (Central) transitions to FAULT state
- Signal set to RED automatically
- Syslog alert generated
- SCADA UI shows offline status

## Assessment
- Was the failure detected automatically?
- How long before the alert was generated?
- Did the safety system respond correctly?
