import os
import sqlite3
import time
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_NAME = "sonix_global.db"
MAX_MESSAGES = 200

# --- DATABASE LOGIC ---
def get_db_connection():
    # Timeout 20s and WAL mode allow multiple users to chat without "Database Locked" errors
    conn = sqlite3.connect(DB_NAME, timeout=20)
    conn.row_factory = sqlite3.Row
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

# --- ROUTES ---
@app.route('/')
def home():
    return "Sonix Precision Server: ONLINE", 200

@app.route('/send', methods=['POST'])
def send_global():
    try:
        data = request.json
        p_name = data.get('PlayerName', 'Unknown')
        u_id = data.get('UserId', 0)
        msg = data.get('Message', '')

        if not msg:
            return jsonify({"status": "empty"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert new message
        cursor.execute("INSERT INTO global_messages (player_name, user_id, message, timestamp) VALUES (?, ?, ?, ?)",
                  (p_name, u_id, msg, time.time()))
        
        # Auto-delete old messages (Keep only the last 200)
        cursor.execute('''DELETE FROM global_messages WHERE id NOT IN 
                          (SELECT id FROM global_messages ORDER BY id DESC LIMIT ?)''', (MAX_MESSAGES,))
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 500

@app.route('/get_messages', methods=['GET'])
def get_global():
    try:
        after = float(request.args.get('after', 0))
        conn = get_db_connection()
        # Fetch newest messages sent by ANY user
        rows = conn.execute("SELECT player_name, user_id, message, timestamp FROM global_messages WHERE timestamp > ? ORDER BY id ASC", (after,)).fetchall()
        conn.close()

        results = []
        for r in rows:
            results.append({
                "PlayerName": r['player_name'],
                "UserId": r['user_id'],
                "Message": r['message'],
                "Timestamp": r['timestamp']
            })
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"status": "error", "reason": str(e)}), 500

# --- RENDER 24/7 TRICK ---
# We use a simple background timer that does NOT use the requests library to avoid boot crashes
def stay_awake():
    while True:
        # Just print to logs to keep the process active in Render's view
        time.sleep(60)
        print("Sonix Heartbeat: Active")

if __name__ == '__main__':
    init_db()
    # Start the heartbeat thread
    threading.Thread(target=stay_awake, daemon=True).start()
    # Use environment port for Render compatibility
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
