import os
import sqlite3
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_NAME = "sonix_global.db"

# --- DATABASE CONNECTION ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn

# --- API ROUTES ---

@app.route('/')
def health_check():
    return "Sonix API: ACTIVE", 200

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    name, uid, msg = data.get('PlayerName'), data.get('UserId'), data.get('Message')
    
    if not all([name, uid, msg]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
        
    with get_db_connection() as conn:
        conn.execute('INSERT INTO global_chat (name, uid, content, timestamp) VALUES (?, ?, ?, ?)', 
                     (name, uid, msg, time.time()))
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
