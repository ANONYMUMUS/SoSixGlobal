import os
import sqlite3
import time
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_NAME = "sonix_global.db"
MAX_MESSAGES = 200

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=15)
    # WAL mode allows reading while writing (crucial for high traffic)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

# --- DATABASE INITIALIZATION ---
def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS global_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                uid INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        conn.commit()

init_db()

# --- ROUTES ---

@app.route('/')
def health_check():
    return "Sonix Precision Server: ONLINE", 200

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    # Matching the Lua Keys exactly
    name = data.get('PlayerName')
    uid = data.get('UserId')
    msg = data.get('Message')

    if not all([name, uid, msg]):
        return jsonify({"status": "error", "reason": "Missing fields"}), 400

    with get_db_connection() as conn:
        # Insert new message
        conn.execute(
            'INSERT INTO global_chat (name, uid, content, timestamp) VALUES (?, ?, ?, ?)',
            (name, uid, msg, time.time())
        )
        # 200 Message Enforcement: Delete everything except the top 200 IDs
        conn.execute('''
            DELETE FROM global_chat 
            WHERE id NOT IN (
                SELECT id FROM global_chat 
                ORDER BY timestamp DESC 
                LIMIT ?
            )
        ''', (MAX_MESSAGES,))
        conn.commit()

    return jsonify({"status": "success"}), 200

@app.route('/get_messages', methods=['GET'])
def get_messages():
    after_ts = request.args.get('after', default=0, type=float)
    
    with get_db_connection() as conn:
        rows = conn.execute(
            'SELECT name, uid, content, timestamp FROM global_chat WHERE timestamp > ? ORDER BY timestamp ASC',
            (after_ts,)
        ).fetchall()
        
    # Formatting to match the Lua table expectations
    output = []
    for r in rows:
        output.append({
            "PlayerName": r['name'],
            "UserId": r['uid'],
            "Message": r['content'],
            "Timestamp": r['timestamp']
        })
        
    return jsonify(output)

# --- RENDER STAY-AWAKE HEARTBEAT ---
def heartbeat():
    while True:
        # Prints to the Render console to keep the process active
        print(f"Sonix Heartbeat: {time.ctime()} - Database size: {os.path.getsize(DB_NAME) if os.path.exists(DB_NAME) else 0} bytes")
        time.sleep(600) # Runs every 10 minutes

if __name__ == '__main__':
    threading.Thread(target=heartbeat, daemon=True).start()
    # Use environment port for Render deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
