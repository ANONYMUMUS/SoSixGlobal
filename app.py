import os
import sqlite3
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_NAME = "sonix_global.db"
MAX_MESSAGES = 200

# --- ADMIN CONFIG ---
# Add UserIDs here to block them from chatting (e.g., [123456, 987654])
BLACKLIST = [] 

# --- DATABASE LOGIC (DO NOT DELETE) ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

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

# --- ROUTES ---

@app.route('/')
def health_check():
    return "Sonix Precision API: ONLINE", 200

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    name, uid, msg = data.get('PlayerName'), data.get('UserId'), data.get('Message')
    
    if not all([name, uid, msg]):
        return jsonify({"status": "error"}), 400

    # BLACKLIST CHECK
    if uid in BLACKLIST:
        return jsonify({"status": "banned"}), 403
    
    with get_db_connection() as conn:
        conn.execute('INSERT INTO global_chat (name, uid, content, timestamp) VALUES (?, ?, ?, ?)', 
                     (name, uid, msg, time.time()))
        conn.execute('DELETE FROM global_chat WHERE id NOT IN (SELECT id FROM global_chat ORDER BY timestamp DESC LIMIT ?)', (MAX_MESSAGES,))
        conn.commit()
    return jsonify({"status": "success"}), 200

@app.route('/get_messages', methods=['GET'])
def get_messages():
    after_ts = request.args.get('after', default=0, type=float)
    with get_db_connection() as conn:
        rows = conn.execute('SELECT name, uid, content, timestamp FROM global_chat WHERE timestamp > ? ORDER BY timestamp ASC', 
                            (after_ts,)).fetchall()
    output = [{"PlayerName": r['name'], "UserId": r['uid'], "Message": r['content'], "Timestamp": r['timestamp']} for r in rows]
    return jsonify(output)

# --- THE EXECUTE ---
if __name__ == '__main__':
    init_db() 
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
