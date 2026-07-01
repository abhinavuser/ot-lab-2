#!/usr/bin/env python3
"""
Railroad North - CTF Flag Server
Day 2 Challenge Validation & Scoreboard
"""

import json
import logging
import os
import hashlib
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

logging.basicConfig(level='INFO', format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============================================================================
# CTF CHALLENGES & FLAGS
# ============================================================================

CHALLENGES = {
    "recon-1": {
        "id": "recon-1",
        "title": "Network Reconnaissance",
        "category": "Reconnaissance",
        "points": 100,
        "difficulty": "Easy",
        "description": "Using Wireshark, identify the IP address of the Master PLC on the OT network. The flag is the full IP address.",
        "hint": "Filter for HTTP traffic on port 8080. Which IP is responding to /api/status requests?",
        "flag": "172.25.0.10"
    },
    "recon-2": {
        "id": "recon-2",
        "title": "Protocol Identification",
        "category": "Reconnaissance",
        "points": 100,
        "difficulty": "Easy",
        "description": "What port does the Master PLC listen on for Modbus TCP connections? The flag is the port number.",
        "hint": "Check the docker-compose.yml or use Wireshark to look for traffic on the standard Modbus port.",
        "flag": "502"
    },
    "exploit-1": {
        "id": "exploit-1",
        "title": "Unauthorized Track Switch",
        "category": "Exploitation",
        "points": 200,
        "difficulty": "Medium",
        "description": "Using curl or a script, send an unauthorized command to switch Segment 1 to ROUTE_C without using the SCADA dashboard. The flag is the value of the 'requested_route' field in the API response.",
        "hint": "POST to the Master PLC's /api/command endpoint with the right JSON payload.",
        "flag": "ROUTE_C"
    },
    "exploit-2": {
        "id": "exploit-2",
        "title": "Sensor Spoofing",
        "category": "Exploitation",
        "points": 250,
        "difficulty": "Medium",
        "description": "Spoof the occupancy sensor on Slave PLC 1 to report FALSE (clear track). Find the name of the device you manipulated. The flag is the exact device name from the API response.",
        "hint": "POST to Slave PLC 1's /api/device/set endpoint. Look for the 'device' field in the response.",
        "flag": "Occupancy North"
    },
    "forensics-1": {
        "id": "forensics-1",
        "title": "Log Correlation",
        "category": "Forensics",
        "points": 300,
        "difficulty": "Hard",
        "description": "After running the flood attack (Attack 3), check the Master PLC logs. How many total commands were recorded? The flag is the exact number shown in the 'total_commands' field of /api/status.",
        "hint": "Use curl to GET the Master PLC /api/status after running the flood. Look at the total_commands field.",
        "flag": "DYNAMIC"
    },
    "forensics-2": {
        "id": "forensics-2",
        "title": "Packet Capture Analysis",
        "category": "Forensics",
        "points": 300,
        "difficulty": "Hard",
        "description": "Using Wireshark, capture traffic while running Attack 1. Find the HTTP POST request body. What is the exact JSON key used to specify the track segment? The flag is that key name.",
        "hint": "Filter Wireshark for 'http.request.method == POST'. Follow the TCP stream and read the JSON body.",
        "flag": "segment_id"
    },
    "defense-1": {
        "id": "defense-1",
        "title": "Emergency Recovery",
        "category": "Defense",
        "points": 200,
        "difficulty": "Medium",
        "description": "Trigger a heartbeat failure by stopping a Slave PLC, then perform a full recovery. What is the exact value of the 'action' field returned by the /api/emergency/clear endpoint?",
        "hint": "docker stop a slave, wait for E-STOP, then docker start it back. POST to /api/emergency/clear and read the response.",
        "flag": "emergency_cleared"
    },
    "defense-2": {
        "id": "defense-2",
        "title": "Safety Interlock Validation",
        "category": "Defense",
        "points": 350,
        "difficulty": "Hard",
        "description": "Attempt to switch Segment 2 to ROUTE_A while Segment 1 is already on ROUTE_A. The safety interlock should block this. What is the exact 'reason' text returned in the rejected command?",
        "hint": "First set Segment 1 to ROUTE_A, then try Segment 2 to ROUTE_A. Check the API response for the rejection reason.",
        "flag": "Conflicting routes at junction"
    }
}

# Team scores
teams = {}

# ============================================================================
# WEB UI
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Railroad North CTF - Scoreboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #000000;
            --panel: #0a0a0a;
            --border: #1a1a1a;
            --text: #e5e5e5;
            --muted: #666666;
            --green: #22c55e;
            --red: #ef4444;
            --yellow: #eab308;
            --blue: #3b82f6;
            --purple: #a855f7;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 40px;
            min-height: 100vh;
        }

        .header {
            text-align: center;
            margin-bottom: 50px;
            padding-bottom: 30px;
            border-bottom: 1px solid var(--border);
        }
        .header h1 {
            font-size: 28px;
            font-weight: 300;
            letter-spacing: 4px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .header p {
            color: var(--muted);
            font-size: 13px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        .layout { display: grid; grid-template-columns: 1fr 380px; gap: 40px; }

        .challenges-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

        .challenge {
            border: 1px solid var(--border);
            padding: 24px;
            position: relative;
            transition: border-color 0.2s;
        }
        .challenge:hover { border-color: #333; }
        .challenge.solved { border-color: var(--green); opacity: 0.6; }
        .challenge.solved::after {
            content: 'SOLVED';
            position: absolute;
            top: 12px;
            right: 12px;
            color: var(--green);
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            letter-spacing: 1px;
        }

        .challenge-cat {
            font-size: 11px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        .challenge h3 {
            font-size: 15px;
            font-weight: 500;
            margin-bottom: 10px;
        }
        .challenge p {
            font-size: 12px;
            color: var(--muted);
            line-height: 1.6;
            margin-bottom: 16px;
        }

        .meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .points {
            font-family: 'JetBrains Mono', monospace;
            font-size: 20px;
            font-weight: 600;
        }
        .difficulty {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 4px 10px;
            border: 1px solid var(--border);
        }
        .difficulty.Easy { color: var(--green); border-color: rgba(34,197,94,0.3); }
        .difficulty.Medium { color: var(--yellow); border-color: rgba(234,179,8,0.3); }
        .difficulty.Hard { color: var(--red); border-color: rgba(239,68,68,0.3); }

        .flag-input {
            display: flex;
            gap: 8px;
        }
        .flag-input input {
            flex: 1;
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            outline: none;
        }
        .flag-input input:focus { border-color: #444; }
        .flag-input button {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--muted);
            padding: 10px 18px;
            cursor: pointer;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.2s;
        }
        .flag-input button:hover {
            border-color: var(--text);
            color: var(--text);
        }

        .hint-btn {
            background: none;
            border: none;
            color: var(--muted);
            font-size: 11px;
            cursor: pointer;
            text-decoration: underline;
            margin-top: 10px;
        }
        .hint {
            display: none;
            margin-top: 10px;
            padding: 10px;
            border: 1px solid rgba(234,179,8,0.2);
            font-size: 11px;
            color: var(--yellow);
            font-family: 'JetBrains Mono', monospace;
        }

        /* Sidebar */
        .sidebar h2 {
            font-size: 14px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--muted);
            margin-bottom: 20px;
        }

        .team-register {
            border: 1px solid var(--border);
            padding: 20px;
            margin-bottom: 30px;
        }
        .team-register input {
            width: 100%;
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 10px 14px;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            margin-bottom: 10px;
            outline: none;
        }
        .team-register button {
            width: 100%;
            background: transparent;
            border: 1px solid var(--border);
            color: var(--muted);
            padding: 12px;
            cursor: pointer;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.2s;
        }
        .team-register button:hover {
            border-color: var(--green);
            color: var(--green);
        }

        .scoreboard-entry {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid var(--border);
        }
        .rank {
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--muted);
            width: 30px;
        }
        .team-name { flex: 1; font-size: 14px; }
        .team-score {
            font-family: 'JetBrains Mono', monospace;
            font-size: 16px;
            font-weight: 600;
            color: var(--green);
        }

        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 30px;
        }
        .stat {
            border: 1px solid var(--border);
            padding: 16px;
            text-align: center;
        }
        .stat-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 24px;
            font-weight: 600;
        }
        .stat-label {
            font-size: 10px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 6px;
        }

        .result-msg {
            margin-top: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            min-height: 16px;
        }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--border); }
    </style>
</head>
<body>
    <div class="header">
        <h1>Railroad North CTF</h1>
        <p>OT Security Capture The Flag -- Day 2</p>
    </div>

    <div class="layout">
        <div>
            <div class="challenges-grid" id="challenges"></div>
        </div>

        <div class="sidebar">
            <div class="team-register">
                <h2>Register Team</h2>
                <input type="text" id="team-name" placeholder="Enter team name">
                <button onclick="registerTeam()">Join CTF</button>
                <div id="team-status" style="margin-top:10px;font-size:12px;color:var(--muted)"></div>
            </div>

            <h2>Scoreboard</h2>
            <div id="scoreboard"></div>

            <div class="stats" id="stats"></div>
        </div>
    </div>

    <script>
        let currentTeam = localStorage.getItem('ctf_team') || '';
        let solvedChallenges = JSON.parse(localStorage.getItem('ctf_solved') || '[]');

        async function loadChallenges() {
            const resp = await fetch('/api/challenges');
            const challenges = await resp.json();

            const grid = document.getElementById('challenges');
            grid.innerHTML = challenges.map(ch => {
                const solved = solvedChallenges.includes(ch.id);
                return '<div class="challenge ' + (solved ? 'solved' : '') + '" id="ch-' + ch.id + '">' +
                    '<div class="challenge-cat">' + ch.category + '</div>' +
                    '<div class="meta">' +
                        '<span class="points">' + ch.points + '</span>' +
                        '<span class="difficulty ' + ch.difficulty + '">' + ch.difficulty + '</span>' +
                    '</div>' +
                    '<h3>' + ch.title + '</h3>' +
                    '<p>' + ch.description + '</p>' +
                    '<div class="flag-input">' +
                        '<input type="text" id="flag-' + ch.id + '" placeholder="Enter flag...">' +
                        '<button onclick="submitFlag(\'' + ch.id + '\')">Submit</button>' +
                    '</div>' +
                    '<div class="result-msg" id="result-' + ch.id + '"></div>' +
                    '<button class="hint-btn" onclick="toggleHint(\'' + ch.id + '\')">Show Hint (-50 pts)</button>' +
                    '<div class="hint" id="hint-' + ch.id + '">' + ch.hint + '</div>' +
                '</div>';
            }).join('');
        }

        async function registerTeam() {
            const name = document.getElementById('team-name').value.trim();
            if (!name) return;

            const resp = await fetch('/api/team/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({team: name})
            });
            const data = await resp.json();

            if (data.success) {
                currentTeam = name;
                localStorage.setItem('ctf_team', name);
                document.getElementById('team-status').innerHTML =
                    '<span style="color:var(--green)">Registered as: ' + name + '</span>';
            }
            loadScoreboard();
        }

        async function submitFlag(challengeId) {
            if (!currentTeam) {
                alert('Register your team first!');
                return;
            }

            const flag = document.getElementById('flag-' + challengeId).value.trim();
            const resp = await fetch('/api/flag/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({team: currentTeam, challenge_id: challengeId, flag: flag})
            });
            const data = await resp.json();

            const el = document.getElementById('result-' + challengeId);
            if (data.correct) {
                el.innerHTML = '<span style="color:var(--green)">Correct! +' + data.points + ' pts</span>';
                solvedChallenges.push(challengeId);
                localStorage.setItem('ctf_solved', JSON.stringify(solvedChallenges));
                document.getElementById('ch-' + challengeId).classList.add('solved');
            } else {
                el.innerHTML = '<span style="color:var(--red)">Incorrect. Try again.</span>';
            }
            loadScoreboard();
        }

        function toggleHint(challengeId) {
            const el = document.getElementById('hint-' + challengeId);
            el.style.display = el.style.display === 'block' ? 'none' : 'block';
        }

        async function loadScoreboard() {
            const resp = await fetch('/api/scoreboard');
            const data = await resp.json();

            document.getElementById('scoreboard').innerHTML = data.teams.map((t, i) =>
                '<div class="scoreboard-entry">' +
                    '<span class="rank">#' + (i + 1) + '</span>' +
                    '<span class="team-name">' + t.name + '</span>' +
                    '<span class="team-score">' + t.score + '</span>' +
                '</div>'
            ).join('');

            document.getElementById('stats').innerHTML =
                '<div class="stat"><div class="stat-value">' + data.teams.length + '</div><div class="stat-label">Teams</div></div>' +
                '<div class="stat"><div class="stat-value">' + data.total_solves + '</div><div class="stat-label">Total Solves</div></div>' +
                '<div class="stat"><div class="stat-value">' + data.max_points + '</div><div class="stat-label">Max Points</div></div>' +
                '<div class="stat"><div class="stat-value">' + Object.keys(data.challenges_solved || {}).length + '</div><div class="stat-label">Unique Solved</div></div>';
        }

        // Restore team
        if (currentTeam) {
            document.getElementById('team-name').value = currentTeam;
            document.getElementById('team-status').innerHTML =
                '<span style="color:var(--green)">Registered as: ' + currentTeam + '</span>';
        }

        loadChallenges();
        loadScoreboard();
        setInterval(loadScoreboard, 5000);
    </script>
</body>
</html>
'''

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/challenges', methods=['GET'])
def get_challenges():
    public = []
    for ch in CHALLENGES.values():
        public.append({
            'id': ch['id'],
            'title': ch['title'],
            'category': ch['category'],
            'points': ch['points'],
            'difficulty': ch['difficulty'],
            'description': ch['description'],
            'hint': ch.get('hint', '')
        })
    return jsonify(sorted(public, key=lambda x: x['points']))

@app.route('/api/team/register', methods=['POST'])
def register_team():
    data = request.json
    team_name = data.get('team', '').strip()
    if not team_name:
        return jsonify({'success': False, 'error': 'Team name required'})
    
    if team_name not in teams:
        teams[team_name] = {
            'name': team_name,
            'score': 0,
            'solved': [],
            'registered_at': datetime.now().isoformat()
        }
        logger.info(f"Team registered: {team_name}")
    
    return jsonify({'success': True, 'team': team_name})

@app.route('/api/flag/submit', methods=['POST'])
def submit_flag():
    data = request.json
    team_name = data.get('team', '').strip()
    challenge_id = data.get('challenge_id', '')
    submitted_flag = data.get('flag', '').strip()
    
    if team_name not in teams:
        return jsonify({'correct': False, 'error': 'Team not registered'})
    
    if challenge_id not in CHALLENGES:
        return jsonify({'correct': False, 'error': 'Invalid challenge'})
    
    challenge = CHALLENGES[challenge_id]
    team = teams[team_name]
    
    if challenge_id in team['solved']:
        return jsonify({'correct': True, 'points': 0, 'message': 'Already solved'})
    
    # Dynamic flag check for forensics-1
    if challenge_id == 'forensics-1':
        try:
            flag_int = int(submitted_flag)
            if flag_int >= 50:
                team['solved'].append(challenge_id)
                team['score'] += challenge['points']
                logger.info(f"Team {team_name} solved {challenge_id} (dynamic: {submitted_flag})")
                return jsonify({'correct': True, 'points': challenge['points']})
        except ValueError:
            pass
        return jsonify({'correct': False})
    
    # Standard flag check
    if submitted_flag.lower() == challenge['flag'].lower():
        team['solved'].append(challenge_id)
        team['score'] += challenge['points']
        logger.info(f"Team {team_name} solved {challenge_id}")
        return jsonify({'correct': True, 'points': challenge['points']})
    
    logger.info(f"Team {team_name} wrong flag for {challenge_id}: {submitted_flag}")
    return jsonify({'correct': False})

@app.route('/api/scoreboard', methods=['GET'])
def scoreboard():
    sorted_teams = sorted(teams.values(), key=lambda t: t['score'], reverse=True)
    
    challenges_solved = {}
    total_solves = 0
    for t in teams.values():
        total_solves += len(t['solved'])
        for ch_id in t['solved']:
            challenges_solved[ch_id] = challenges_solved.get(ch_id, 0) + 1
    
    return jsonify({
        'teams': [{'name': t['name'], 'score': t['score'], 'solved_count': len(t['solved'])} for t in sorted_teams],
        'total_solves': total_solves,
        'max_points': sum(ch['points'] for ch in CHALLENGES.values()),
        'challenges_solved': challenges_solved
    })

if __name__ == '__main__':
    logger.info("Starting CTF Flag Server on 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
