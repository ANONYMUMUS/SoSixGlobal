import os
import sqlite3
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
# Render uses a temporary filesystem; using /tmp/ can sometimes help with permissions
DB_NAME = "sonix_global.db"
MAX_MESSAGES = 200

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=15)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS global_chat 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, uid INTEGER, content TEXT, timestamp REAL)''')
        conn.close()

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    if not data: return jsonify({"status": "error"}), 400
    
    name = data.get('PlayerName')
    uid = data.get('UserId')
    msg = data.get('Message')
    
    conn = get_db_connection()
    if not conn: return jsonify({"status": "db_error"}), 500

    try:
        with conn:
            conn.execute('INSERT INTO global_chat (name, uid, content, timestamp) VALUES (?, ?, ?, ?)', 
                         (name, uid, msg, time.time()))
            conn.execute('DELETE FROM global_chat WHERE id NOT IN (SELECT id FROM global_chat ORDER BY timestamp DESC LIMIT ?)', (MAX_MESSAGES,))
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"SEND ERROR: {e}")
        return jsonify({"status": "error"}), 500
    finally:
        conn.close()

@app.route('/get_messages', methods=['GET'])
def get_messages():
    after_ts = request.args.get('after', default=0, type=float)
    conn = get_db_connection()
    if not conn: return jsonify([]), 500

    try:
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
        print(f"GET_MESSAGES CRASH: {e}") # Check your Render Logs for this!
        return jsonify([]), 500
    finally:
        conn.close()

@app.route('/')
def health():
    return "Sonix Precision API: ONLINE", 200

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
