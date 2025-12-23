from flask import Flask, request, jsonify
import sqlite3
import time
import threading
import requests

app = Flask(__name__)
DB_NAME = "sonix_global.db"
SELF_URL = "https://sosixglobal.onrender.com/ping" 

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10) # Timeout prevents "Database is locked" errors
    conn.row_factory = sqlite3.Row
    # Enable WAL mode so multiple users can read/write simultaneously
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS global_messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  player_name TEXT, 
                  user_id INTEGER, 
                  message TEXT, 
                  timestamp REAL)''')
    conn.commit()
    conn.close()

# 24/7 Keep-Alive
def keep_alive():
    while True:
        try:
            requests.get(SELF_URL)
        except:
            pass
        time.sleep(60)

@app.route('/ping')
def ping():
    return "Online", 200

@app.route('/send', methods=['POST'])
def send_global():
    data = request.json
    p_name = data.get('PlayerName', 'Unknown')
    u_id = data.get('UserId', 0)
    msg = data.get('Message', '')

    if not msg:
        return jsonify({"status": "empty"}), 400

    conn = get_db_connection()
    conn.execute("INSERT INTO global_messages (player_name, user_id, message, timestamp) VALUES (?, ?, ?, ?)",
              (p_name, u_id, msg, time.time()))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/get_messages', methods=['GET'])
def get_global():
    after = float(request.args.get('after', 0))
    conn = get_db_connection()
    # Fetch all messages from everyone after the last timestamp
    rows = conn.execute("SELECT player_name, user_id, message, timestamp FROM global_messages WHERE timestamp > ? ORDER BY timestamp ASC", (after,)).fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "PlayerName": r['player_name'],
            "UserId": r['user_id'],
            "Message": r['message'],
            "Timestamp": r['timestamp']
        })
    return jsonify(results)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
