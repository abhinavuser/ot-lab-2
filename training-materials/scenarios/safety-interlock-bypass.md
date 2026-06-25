# Scenario 3: Safety Interlock Bypass Attempt

## Objective
Detect attempts to bypass safety rules by switching tracks while occupied.

## Difficulty: Hard | Duration: 30 minutes

## Attack Steps

```bash
# 1. Set occupancy sensor to true (simulate occupied track)
docker exec railroad-slave-plc-1 curl -X POST \
  http://localhost:8080/api/device/set \
  -H "Content-Type: application/json" \
  -d '{"device": "occupancy_sensor", "value": true}'

# 2. Attempt switch command (should be rejected)
docker exec railroad-dmz-pentest curl -X POST \
  http://172.25.1.10:8080/api/device/switch \
  -H "Content-Type: application/json" \
  -d '{"switch_id": 1, "command": "ACTIVATE"}'

# 3. Check audit logs for safety interlock trigger
docker logs railroad-slave-plc-1 | grep -i "cannot\|rejected"
docker logs railroad-collector | grep REJECTED

# 4. Reset occupancy sensor
docker exec railroad-slave-plc-1 curl -X POST \
  http://localhost:8080/api/device/set \
  -H "Content-Type: application/json" \
  -d '{"device": "occupancy_sensor", "value": false}'
```

## Expected Logs
```
[REJECTED] Cannot activate switch 1: track occupied
[AUDIT] Safety interlock rule 3 triggered
```

## Assessment
- Was the safety interlock enforced?
- Were proper audit logs generated?
- Can you identify which rule was triggered?
