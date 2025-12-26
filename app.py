import os
import sqlite3
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_NAME = "sonix_global.db"
MAX_MESSAGES = 200

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=15)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row  # Crucial for matching the keys in your script
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS global_chat 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, uid INTEGER, content TEXT, timestamp REAL)''')
        conn.commit()

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    if not data: return jsonify({"status": "error"}), 400
    
    name = data.get('PlayerName')
    uid = data.get('UserId')
    msg = data.get('Message')
    
    if not all([name, uid, msg]):
        return jsonify({"status": "error"}), 400
    
    with get_db_connection() as conn:
        conn.execute('INSERT INTO global_chat (name, uid, content, timestamp) VALUES (?, ?, ?, ?)', 
                     (name, uid, msg, time.time()))
        # Auto-clean old messages to keep server fast
        conn.execute('DELETE FROM global_chat WHERE id NOT IN (SELECT id FROM global_chat ORDER BY timestamp DESC LIMIT ?)', (MAX_MESSAGES,))
        conn.commit()
    return jsonify({"status": "success"}), 200

@app.route('/get_messages', methods=['GET'])
def get_messages():
    try:
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
    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify([]), 500

@app.route('/')
def health():
    return "Sonix Precision API: ONLINE", 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
