# Scenario 4: Modbus Protocol Manipulation

## Objective
Detect malformed/abnormal Modbus traffic on the OT network.

## Difficulty: Advanced | Duration: 45 minutes

## Attack Steps

```bash
# Run from OT pentest container
docker exec -it railroad-pentest python3 /app/modbus-attack.py 172.25.0.10 502
```

## Attack Types
1. **Excessive Read** - Request 1000 registers at once
2. **Critical Write** - Write invalid value to setpoint register
3. **Function Probe** - Send unsupported function codes
4. **DoS** - Rapid-fire coil reads (50+ per second)

## Detection
- IDS (Zeek) should generate alerts for:
  - Excessive read requests
  - Write operations to critical registers
  - Unknown function codes
  - Abnormal request frequency
- Check Kibana for Modbus anomaly alerts

## Monitoring Commands
```bash
# View IDS alerts
docker logs railroad-ids

# Check collector for Modbus events
docker logs railroad-collector | grep -i modbus

# View Elasticsearch indices
curl http://localhost:9200/railroad-alerts-*/_search?pretty
```
