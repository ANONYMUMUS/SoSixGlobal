import os
import sqlite3
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_NAME = "sonix_global.db"
MAX_MESSAGES = 200

# --- CONFIG ---
MODERATORS = ["shadowss_99"]

# --- DATABASE LOGIC ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        # Table for Global Chat Messages
        conn.execute('''CREATE TABLE IF NOT EXISTS global_chat 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, uid INTEGER, content TEXT, timestamp REAL)''')
        
        # Table for Penalties (Storage for Bans/Mutes)
        conn.execute('''CREATE TABLE IF NOT EXISTS penalties 
            (uid INTEGER PRIMARY KEY, name TEXT, type TEXT, end_time REAL)''')
        conn.commit()

# --- HELPER: CHECK BANS/MUTES ---
def check_penalty(uid):
    try:
        with get_db_connection() as conn:
            row = conn.execute('SELECT type, end_time FROM penalties WHERE uid = ?', (uid,)).fetchone()
            if row:
                if row['end_time'] == 0 or time.time() < row['end_time']:
                    return row['type'], row['end_time']
                else:
                    # Clean the trash (Auto-unban/unmute)
                    conn.execute('DELETE FROM penalties WHERE uid = ?', (uid,))
                    conn.commit()
    except:
        pass
    return None, None

# --- CHAT ROUTES ---

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    name = data.get('PlayerName')
    uid = data.get('UserId')
    msg = data.get('Message')
    
    if not all([name, uid, msg]):
        return jsonify({"status": "error"}), 400

    # Safety: Check if user is banned or muted before saving message
    p_type, p_end = check_penalty(uid)
    if p_type:
        return jsonify({"status": "restricted", "type": p_type, "expires": p_end}), 403
    
    with get_db_connection() as conn:
        conn.execute('INSERT INTO global_chat (name, uid, content, timestamp) VALUES (?, ?, ?, ?)', 
                     (name, uid, msg, time.time()))
        # Keep storage clean
        conn.execute('DELETE FROM global_chat WHERE id NOT IN (SELECT id FROM global_chat ORDER BY timestamp DESC LIMIT ?)', (MAX_MESSAGES,))
        conn.commit()
    return jsonify({"status": "success"}), 200

@app.route('/get_messages', methods=['GET'])
def get_messages():
    after_ts = request.args.get('after', default=0, type=float)
    with get_db_connection() as conn:
        rows = conn.execute('SELECT name, uid, content, timestamp FROM global_chat WHERE timestamp > ? ORDER BY timestamp ASC', (after_ts,)).fetchall()
    
    output = []
    for r in rows:
        output.append({
            "PlayerName": r['name'],
            "UserId": r['uid'],
            "Message": r['content'],
            "Timestamp": r['timestamp']
        })
    return jsonify(output)

# --- ADMIN ROUTES ---

@app.route('/admin/execute', methods=['POST'])
def execute_command():
    data = request.json
    mod_name = data.get('ModName')
    target_name = data.get('TargetName')
    target_uid = data.get('TargetId')
    action = data.get('Action') # ban, mute, unban, unmute
    duration = data.get('Duration', 0)

    if mod_name not in MODERATORS:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    with get_db_connection() as conn:
        if action in ["ban", "mute"]:
            end_ts = 0 if duration == 0 else time.time() + duration
            conn.execute('INSERT OR REPLACE INTO penalties (uid, name, type, end_time) VALUES (?, ?, ?, ?)', 
                         (target_uid, target_name, action, end_ts))
        else: # Unban/Unmute
            conn.execute('DELETE FROM penalties WHERE uid = ?', (target_uid,))
        conn.commit()
    return jsonify({"status": "success"}), 200

@app.route('/admin/list', methods=['GET'])
def get_blocklist():
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM penalties').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/')
def health():
    return "Sonix Precision API: ONLINE", 200

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
