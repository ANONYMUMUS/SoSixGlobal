from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Storage
messages = []
MAX_HISTORY = 100  # Keep server light

@app.route('/')
def home():
    return "Sonix Precision Server Online"

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    
    # Construct the message object
    msg = {
        "PlayerName": data.get("PlayerName", "Unknown"),
        "UserId": data.get("UserId", 0),
        "Message": data.get("Message", ""),
        "Timestamp": time.time(),
        "Type": data.get("Type", "global"),  # 'global' or 'private'
        "TargetId": data.get("TargetId", None) # Who is it for?
    }
    
    messages.append(msg)
    
    # Keep history clean
    if len(messages) > MAX_HISTORY:
        messages.pop(0)
        
    return jsonify({"status": "sent"}), 200

@app.route('/get_messages', methods=['GET'])
def get_messages():
    after_timestamp = float(request.args.get('after', 0))
    requester_id = request.args.get('uid') # The ID of the person asking for messages
    
    new_messages = []
    
    for msg in messages:
        if msg["Timestamp"] > after_timestamp:
            
            # LOGIC: FILTERING
            if msg["Type"] == "global":
                new_messages.append(msg)
                
            elif msg["Type"] == "private":
                # Only show if the requester is the Sender or the Receiver
                # We cast to str/int loosely to match Lua types
                try:
                    r_id = int(requester_id)
                    sender = int(msg["UserId"])
                    target = int(msg["TargetId"])
                    
                    if r_id == sender or r_id == target:
                        new_messages.append(msg)
                except:
                    pass # Invalid ID, ignore message

    return jsonify(new_messages), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
