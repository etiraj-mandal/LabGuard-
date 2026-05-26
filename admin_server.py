from flask import Flask, request, render_template_string, redirect, url_for, jsonify
import mysql.connector
import sys
import random

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
DB_CONFIG = {"host": "localhost", "user": "root", "password": ""}
DB_NAME = "labguard"

active_pins = {}

def setup_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.close()

        db = mysql.connector.connect(**DB_CONFIG, database=DB_NAME)
        cursor = db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pc_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pc_name VARCHAR(100) UNIQUE, 
            cpu FLOAT,
            ram FLOAT,
            blocked_apps VARCHAR(255),
            violation_time VARCHAR(50),
            is_violation BOOLEAN DEFAULT FALSE
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS violation_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pc_name VARCHAR(100),
            details VARCHAR(255),
            v_time VARCHAR(50)
        )
        """)
        db.commit()
        db.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        sys.exit(1)

def get_db():
    conn = mysql.connector.connect(host="localhost", user="root", password="", database=DB_NAME)
    return conn, conn.cursor(dictionary=True)

setup_database()

# ------------------ UI TEMPLATES ------------------

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LabGuard Pro | Terminal Monitor</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-overlay: rgba(2, 6, 23, 0.85);
            --glass: rgba(255, 255, 255, 0.03);
            --glass-border: rgba(255, 255, 255, 0.12);
            --text-main: #ffffff;
            --text-muted: rgba(255, 255, 255, 0.5);
            --primary: #00f2fe;
            --danger: #ff4b2b;
            --success: #00ff87;
            --header-bg: rgba(15, 23, 42, 0.8);
            --glow: 0 0 15px rgba(0, 242, 254, 0.4);
        }

        [data-theme="light"] {
            --bg-overlay: rgba(248, 250, 252, 0.8);
            --glass: rgba(255, 255, 255, 0.7);
            --glass-border: rgba(0, 0, 0, 0.08);
            --text-main: #0f172a;
            --text-muted: #64748b;
            --primary: #4f46e5;
            --danger: #ef4444;
            --success: #10b981;
            --header-bg: rgba(255, 255, 255, 0.9);
            --glow: 0 4px 12px rgba(79, 70, 229, 0.2);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; transition: background 0.4s, color 0.4s; }
        
        body { 
            background: linear-gradient(var(--bg-overlay), var(--bg-overlay)), url('/static/iiiiiiiiiiiiiiii.jpg'); 
            background-size: cover; background-attachment: fixed; color: var(--text-main); min-height: 100vh;
        }

        header {
            background: var(--header-bg); backdrop-filter: blur(20px); padding: 1rem 5%;
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 1px solid var(--glass-border); position: sticky; top: 0; z-index: 1000;
        }

        .brand { display: flex; align-items: center; gap: 12px; text-decoration: none; color: inherit; }
        .brand i { font-size: 1.6rem; color: var(--primary); text-shadow: var(--glow); }
        .brand h1 { font-size: 1.3rem; font-weight: 800; }

        .theme-btn {
            background: var(--glass); border: 1px solid var(--glass-border); color: var(--text-main);
            padding: 10px 18px; border-radius: 50px; cursor: pointer; font-size: 0.85rem;
            font-weight: 700; display: flex; align-items: center; gap: 10px; backdrop-filter: blur(10px);
        }

        .wrapper { max-width: 1400px; margin: 2.5rem auto; padding: 0 25px; }

        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-bottom: 3rem; }
        .stat-card {
            background: var(--glass); backdrop-filter: blur(15px); padding: 1.8rem; border-radius: 24px; 
            border: 1px solid var(--glass-border); display: flex; align-items: center; gap: 25px;
        }
        .stat-icon { width: 55px; height: 55px; border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; }
        .icon-p { background: rgba(0, 242, 254, 0.1); color: var(--primary); }
        .icon-d { background: rgba(255, 75, 43, 0.1); color: var(--danger); }

        .glass-panel {
            background: var(--glass); backdrop-filter: blur(25px); border-radius: 30px; 
            border: 1px solid var(--glass-border); overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.2);
        }

        table { width: 100%; border-collapse: collapse; }
        th { background: rgba(0,0,0,0.1); padding: 1.5rem; text-align: left; color: var(--primary); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; }
        td { padding: 1.5rem; border-bottom: 1px solid var(--glass-border); }

        .pc-link { color: inherit; text-decoration: none; font-weight: 800; }
        .pc-link:hover { color: var(--primary); }

        .res-container { width: 100%; max-width: 180px; }
        .res-info { display: flex; justify-content: space-between; font-size: 0.65rem; font-weight: 800; margin-bottom: 6px; }
        .bar-track { width: 100%; height: 7px; background: rgba(255,255,255,0.05); border-radius: 20px; overflow: hidden; }
        .bar-thumb { height: 100%; border-radius: 20px; }
        .bg-primary { background: linear-gradient(90deg, var(--primary), #4f46e5); box-shadow: 0 0 12px var(--primary); }
        .bg-danger { background: var(--danger); box-shadow: 0 0 12px var(--danger); }

        .status-badge { padding: 8px 16px; border-radius: 50px; font-size: 0.7rem; font-weight: 800; border: 1px solid rgba(0, 255, 135, 0.2); color: var(--success); background: rgba(0, 255, 135, 0.05); }
        .status-badge.alert { color: var(--danger); border-color: var(--danger); background: rgba(255, 75, 43, 0.05); animation: pulse-red 2s infinite; }
        
        .action-btn { background: var(--danger); color: white; padding: 12px 24px; border-radius: 14px; text-decoration: none; font-size: 0.7rem; font-weight: 800; box-shadow: 0 5px 20px rgba(255, 75, 43, 0.4); display: inline-flex; align-items: center; gap: 8px; }
        
        @keyframes pulse-red { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
    </style>
</head>
<body>
<header>
    <a href="/" class="brand"><i class="fas fa-fingerprint"></i><h1>LABGUARD<span>PRO</span></h1></a>
    <button class="theme-btn" onclick="toggleTheme()">
        <i id="mode-icon" class="fas fa-sun"></i>
        <span id="mode-text">Day Mode</span>
    </button>
</header>

<div class="wrapper">
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-icon icon-p"><i class="fas fa-microchip"></i></div>
            <div class="stat-info">
                <h4 style="color: var(--text-muted); font-size: 0.7rem;">Active Nodes</h4>
                <p style="font-size: 1.6rem; font-weight: 800;">{{ total_pcs }}</p>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon icon-d"><i class="fas fa-shield-virus"></i></div>
            <div class="stat-info">
                <h4 style="color: var(--text-muted); font-size: 0.7rem;">Threats Blocked</h4>
                <p style="font-size: 1.6rem; font-weight: 800;">{{ violations }}</p>
            </div>
        </div>
    </div>

    <div class="glass-panel">
        <table>
            <thead><tr><th>Terminal (History)</th><th>Hardware Load</th><th>Security</th><th>Last Active</th><th>Command</th></tr></thead>
            <tbody>
                {% for pc in pcs %}
                <tr>
                    <td><a href="/history/{{ pc.pc_name }}" class="pc-link"><i class="fas fa-terminal" style="color: var(--primary); margin-right: 12px;"></i>{{ pc.pc_name }}</a></td>
                    <td>
                        <div class="res-container">
                            <div class="res-info"><span>CPU Usage</span><span>{{ pc.cpu }}%</span></div>
                            <div class="bar-track"><div class="bar-thumb {{ 'bg-danger' if pc.cpu > 80 else 'bg-primary' }}" style="width: {{ pc.cpu }}%"></div></div>
                        </div>
                    </td>
                    <td>
                        {% if pc.is_violation %}<div class="status-badge alert"><i class="fas fa-skull"></i> {{ pc.blocked_apps }}</div>
                        {% else %}<div class="status-badge"><i class="fas fa-shield-check"></i> SECURE</div>{% endif %}
                    </td>
                    <td style="font-family: monospace; font-size: 0.75rem; color: var(--text-muted);">{{ pc.violation_time }}</td>
                    <td>
                        {% if pc.is_violation %}<a href="/approve/{{ pc.id }}" class="action-btn"><i class="fas fa-unlock-alt"></i> RELEASE PC</a>
                        {% else %}<i class="fas fa-check-double" style="color: var(--success); opacity: 0.4;"></i>{% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<script>
    function updateUI(theme) {
        const html = document.documentElement;
        const icon = document.getElementById('mode-icon');
        const text = document.getElementById('mode-text');
        html.setAttribute('data-theme', theme);
        if (theme === 'light') {
            icon.className = 'fas fa-moon';
            text.innerText = 'Night Mode';
        } else {
            icon.className = 'fas fa-sun';
            text.innerText = 'Day Mode';
        }
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('labguard-theme', newTheme);
        updateUI(newTheme);
    }

    window.onload = () => {
        const saved = localStorage.getItem('labguard-theme') || 'dark';
        updateUI(saved);
        setTimeout(() => location.reload(), 5000);
    };
</script>
</body>
</html>
"""

HISTORY_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Logs | {{ pc_name }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-overlay: rgba(2, 6, 23, 0.85);
            --glass: rgba(255, 255, 255, 0.03);
            --glass-border: rgba(255, 255, 255, 0.12);
            --text-main: #ffffff;
            --text-muted: rgba(255, 255, 255, 0.5);
            --primary: #00f2fe;
            --danger: #ff4b2b;
            --header-bg: rgba(15, 23, 42, 0.8);
        }

        [data-theme="light"] {
            --bg-overlay: rgba(248, 250, 252, 0.8);
            --glass: rgba(255, 255, 255, 0.7);
            --glass-border: rgba(0, 0, 0, 0.08);
            --text-main: #0f172a;
            --text-muted: #64748b;
            --primary: #4f46e5;
            --header-bg: rgba(255, 255, 255, 0.9);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', sans-serif; }
        
        body { background: linear-gradient(var(--bg-overlay), var(--bg-overlay)), url('/static/iiiiiiiiiiiiiiii.jpg'); background-size: cover; background-attachment: fixed; color: var(--text-main); min-height: 100vh; }

        header { background: var(--header-bg); backdrop-filter: blur(20px); padding: 1rem 5%; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--glass-border); position: sticky; top: 0; z-index: 1000; }

        .back-link { color: var(--primary); text-decoration: none; font-weight: 800; font-size: 0.85rem; display: flex; align-items: center; gap: 8px; padding: 10px 20px; background: var(--glass); border-radius: 50px; border: 1px solid var(--glass-border); }

        .wrapper { max-width: 1100px; margin: 3rem auto; padding: 0 25px; }

        .history-header { margin-bottom: 2rem; border-left: 4px solid var(--primary); padding-left: 20px; }
        .history-header h2 { font-size: 2rem; font-weight: 800; }
        .history-header span { color: var(--primary); }

        .glass-panel { background: var(--glass); backdrop-filter: blur(25px); border-radius: 30px; border: 1px solid var(--glass-border); overflow: hidden; }

        table { width: 100%; border-collapse: collapse; }
        th { background: rgba(0,0,0,0.1); padding: 1.5rem; text-align: left; color: var(--primary); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; }
        td { padding: 1.5rem; border-bottom: 1px solid var(--glass-border); }

        .danger-text { color: var(--danger); font-weight: 700; display: flex; align-items: center; gap: 10px; }
        .time-text { font-family: monospace; color: var(--text-muted); font-size: 0.85rem; }
    </style>
</head>
<body>
<header>
    <h1>LABGUARD<span>PRO</span></h1>
    <a href="/" class="back-link"><i class="fas fa-arrow-left"></i> RETURN TO DASHBOARD</a>
</header>

<div class="wrapper">
    <div class="history-header">
        <h2>Security Logs: <span>{{ pc_name }}</span></h2>
        <p style="color: var(--text-muted);">Historical tracking of all system lock events.</p>
    </div>

    <div class="glass-panel">
        <table>
            <thead><tr><th>Timestamp</th><th>Details / Reason</th><th>Status</th></tr></thead>
            <tbody>
                {% for log in logs %}
                <tr>
                    <td class="time-text">{{ log.v_time }}</td>
                    <td class="danger-text"><i class="fas fa-shield-slash"></i> {{ log.details }}</td>
                    <td><span style="font-size: 0.7rem; font-weight: 800; color: var(--danger); opacity: 0.7;">REPORTED</span></td>
                </tr>
                {% endfor %}
                {% if not logs %}
                <tr><td colspan="3" style="text-align: center; padding: 4rem; color: var(--text-muted);">No records found.</td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</div>
<script>
    window.onload = () => {
        const saved = localStorage.getItem('labguard-theme') || 'dark';
        document.documentElement.setAttribute('data-theme', saved);
    };
</script>
</body>
</html>
"""

# ------------------ ROUTES ------------------

@app.route("/")
def dashboard():
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM pc_logs ORDER BY is_violation DESC, pc_name ASC")
    pcs = cursor.fetchall()
    total_pcs = len(pcs)
    violations = sum(1 for pc in pcs if pc['is_violation'])
    cursor.close(); conn.close()
    return render_template_string(DASHBOARD_PAGE, pcs=pcs, total_pcs=total_pcs, violations=violations)

@app.route("/history/<pc_name>")
def view_history(pc_name):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM violation_history WHERE pc_name = %s ORDER BY id DESC", (pc_name,))
    logs = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template_string(HISTORY_PAGE, pc_name=pc_name, logs=logs)

@app.route("/update", methods=["POST"])
def update():
    conn, cursor = get_db()
    try:
        data = request.get_json()
        pc_name, cpu, ram, curr_time = data["pc_name"], data["cpu"], data["ram"], data["time"]
        status, blocked_list = data.get("status", "MONITORING"), data.get("blocked_apps", [])
        is_violating = True if (status == "LOCKED" or blocked_list) else False
        msg = ", ".join(blocked_list) if blocked_list else "SYSTEM LOCKED"

        if is_violating:
            cursor.execute("INSERT INTO violation_history (pc_name, details, v_time) VALUES (%s, %s, %s)", 
                           (pc_name, msg, curr_time))

        cursor.execute("SELECT is_violation FROM pc_logs WHERE pc_name = %s", (pc_name,))
        existing = cursor.fetchone()
        
        if existing:
            final_state = True if (existing['is_violation'] or is_violating) else False
            cursor.execute("UPDATE pc_logs SET cpu=%s, ram=%s, blocked_apps=%s, violation_time=%s, is_violation=%s WHERE pc_name=%s",
                           (cpu, ram, msg if is_violating else existing['blocked_apps'], curr_time, final_state, pc_name))
        else:
            cursor.execute("INSERT INTO pc_logs (pc_name, cpu, ram, blocked_apps, violation_time, is_violation) VALUES (%s, %s, %s, %s, %s, %s)",
                           (pc_name, cpu, ram, msg if is_violating else "Active", curr_time, is_violating))
        conn.commit()
        return {"status": "success"}
    except: return {"status": "error"}
    finally: cursor.close(); conn.close()

@app.route("/approve/<int:log_id>")
def approve(log_id):
    conn, cursor = get_db()
    cursor.execute("SELECT pc_name FROM pc_logs WHERE id=%s", (log_id,))
    res = cursor.fetchone()
    if res:
        pc_name = res['pc_name']
        active_pins[pc_name] = str(random.randint(1000, 9999))
        cursor.execute("UPDATE pc_logs SET is_violation=FALSE, blocked_apps='✔ Clean' WHERE id=%s", (log_id,))
        conn.commit()
    cursor.close(); conn.close()
    return redirect(url_for('dashboard'))

@app.route("/get_pin/<pc_name>")
def get_pin(pc_name):
    pin = active_pins.get(pc_name)
    if pin:
        del active_pins[pc_name]
        return jsonify({"pin": pin})
    return jsonify({"pin": None})

@app.route("/get_status/<pc_name>")
def get_status(pc_name):
    conn, cursor = get_db()
    cursor.execute("SELECT is_violation FROM pc_logs WHERE pc_name=%s", (pc_name,))
    result = cursor.fetchone()
    cursor.close(); conn.close()
    return jsonify({"is_violation": bool(result['is_violation'])}) if result else jsonify({"is_violation": False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)