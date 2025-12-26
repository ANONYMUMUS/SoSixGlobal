import os
import sqlite3
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
# Using a local path for the database
DB_NAME = "sonix_global.db"
MAX_MESSAGES = 200

def get_db_connection():
    try:
        # We removed the WAL mode here to prevent permission crashes on Render
        conn = sqlite3.connect(DB_NAME, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"!!! DB CONNECT ERROR: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            with conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS global_chat 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, uid INTEGER, content TEXT, timestamp REAL)''')
            print("Database Initialized Successfully")
        except Exception as e:
            print(f"!!! DB INIT ERROR: {e}")
        finally:
            conn.close()

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    if not data: return jsonify({"status": "error"}), 400
    
    name = data.get('PlayerName')
    uid = data.get('UserId')
    msg = data.get('Message')
    
    conn = get_db_connection()
    if not conn: return jsonify({"status": "server_error"}), 500

    try:
        with conn:
            conn.execute('INSERT INTO global_chat (name, uid, content, timestamp) VALUES (?, ?, ?, ?)', 
                         (name, uid, msg, time.time()))
            # Optimization: Keep the database small
            conn.execute('DELETE FROM global_chat WHERE id NOT IN (SELECT id FROM global_chat ORDER BY id DESC LIMIT ?)', (MAX_MESSAGES,))
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"!!! SEND CRASH: {e}")
        return jsonify({"status": "error"}), 500
    finally:
        conn.close()

@app.route('/get_messages', methods=['GET'])
def get_messages():
    try:
        after_ts = request.args.get('after', default=0, type=float)
        conn = get_db_connection()
        if not conn: return jsonify([]), 500

        rows = conn.execute('SELECT name, uid, content, timestamp FROM global_chat WHERE timestamp > ? ORDER BY timestamp ASC', (after_ts,)).fetchall()
        
        output = []
        for r in rows:
            output.append({
                "PlayerName": r['name'],
                "UserId": r['uid'],
                "Message": r['content'],
                "Timestamp": r['timestamp']
            })
        conn.close()
        return jsonify(output)
    except Exception as e:
        print(f"!!! GET_MESSAGES CRASH: {e}")
        return jsonify([]), 500

@app.route('/')
def health():
    return "Sonix Precision API: ONLINE", 200

if __name__ == '__main__':
    init_db()
    # Port must be dynamic for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
