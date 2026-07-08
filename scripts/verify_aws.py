#!/usr/bin/env python3
"""Full AWS verification script"""
import urllib.request, json, sys

def get(url):
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url), timeout=15)
        return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode()), None
    except Exception as e:
        return None, str(e)

def post(url, payload):
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode()), None
    except Exception as e:
        return None, str(e)

BASE = 'http://13.206.102.61'
print('='*60)
print('  FULL AWS VERIFICATION')
print('='*60)
fails = 0

# 1. SCADA
r, e = get(f'{BASE}:8081/health')
if r:
    print(f'[PASS] SCADA Dashboard: {r.get("status","?")}')
else:
    print(f'[FAIL] SCADA Dashboard: {e}'); fails+=1

# 2. Master PLC Status
r, e = get(f'{BASE}:8085/api/status')
if r:
    online = sum(1 for s in r.get('slave_health',{}).values() if s.get('status')=='ONLINE')
    print(f'[PASS] Master PLC: status={r.get("status")}, slaves={online}/3')
    if r.get('firmware_notes') and 'FLAG{modbus_master_pwned}' in r['firmware_notes']:
        print(f'[PASS] CTF-10 hidden flag: PRESENT')
    else:
        print(f'[FAIL] CTF-10 hidden flag: MISSING from firmware_notes'); fails+=1
else:
    print(f'[FAIL] Master PLC: {e}'); fails+=1

# 3. CTF Scoreboard
r, e = get(f'{BASE}:8090/api/challenges')
if r:
    print(f'[PASS] CTF Scoreboard: {len(r)} challenges')
    if len(r) != 10:
        print(f'[WARN] Expected 10 challenges, got {len(r)}'); fails+=1
else:
    print(f'[FAIL] CTF Scoreboard: {e}'); fails+=1

# 4. Attack 1 - Track Switch
r, e = post(f'{BASE}:8085/api/command', {'segment_id': 2, 'route': 'ROUTE_B'})
if r and r.get('success') == True:
    print(f'[PASS] Attack 1 (track switch): OK')
else:
    print(f'[FAIL] Attack 1: {r or e}'); fails+=1

# 5. CTF-9 - API Fuzzing
r, e = post(f'{BASE}:8085/api/command', {'segment_id': 1, 'route': 'ROUTE_XYZ'})
if r and r.get('error') == 'Invalid route: ROUTE_XYZ':
    print(f'[PASS] CTF-9 (API fuzz): error="{r["error"]}"')
else:
    print(f'[FAIL] CTF-9: {r or e}'); fails+=1

# 6. CTF-8 - Safety Interlock WITH reason field
post(f'{BASE}:8085/api/command', {'segment_id': 1, 'route': 'ROUTE_A'})
r, e = post(f'{BASE}:8085/api/command', {'segment_id': 2, 'route': 'ROUTE_A'})
if r:
    if r.get('success') == False and 'reason' in r:
        print(f'[PASS] CTF-8 (interlock): reason="{r["reason"]}"')
    elif r.get('success') == False and 'reason' not in r:
        print(f'[FAIL] CTF-8: Blocked but NO reason field! master_plc.py NOT updated on AWS')
        print(f'       Response was: {r}')
        fails+=1
    else:
        print(f'[FAIL] CTF-8: Did not block! {r}'); fails+=1
else:
    print(f'[FAIL] CTF-8: {e}'); fails+=1

# 7. CTF-7 - Emergency clear
r, e = post(f'{BASE}:8085/api/emergency/clear', {})
if r and r.get('action') == 'emergency_cleared':
    print(f'[PASS] CTF-7 (emergency clear): OK')
else:
    print(f'[FAIL] CTF-7: {r or e}'); fails+=1

# 8. CTF-3 - ROUTE_C
r, e = post(f'{BASE}:8085/api/command', {'segment_id': 1, 'route': 'ROUTE_C'})
if r and r.get('requested_route') == 'ROUTE_C':
    print(f'[PASS] CTF-3 (ROUTE_C): OK')
else:
    print(f'[FAIL] CTF-3: {r or e}'); fails+=1

# 9. CTF team + flag
r, e = post(f'{BASE}:8090/api/team/register', {'team': 'VerifyTest2'})
if r and r.get('success'):
    print(f'[PASS] CTF registration: OK')
else:
    print(f'[FAIL] CTF registration: {r or e}'); fails+=1

r, e = post(f'{BASE}:8090/api/flag/submit', {'team': 'VerifyTest2', 'challenge_id': 'recon-2', 'flag': '502'})
if r and r.get('correct'):
    print(f'[PASS] CTF flag submit: recon-2 correct (+{r.get("points")} pts)')
else:
    print(f'[FAIL] CTF flag submit: {r or e}'); fails+=1

print()
print('='*60)
if fails == 0:
    print('  ALL CHECKS PASSED. You are good to go.')
else:
    print(f'  {fails} CHECK(S) FAILED. Fix these before tomorrow!')
print('='*60)
