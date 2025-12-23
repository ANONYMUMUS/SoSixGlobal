from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# We use a tiny script first to make sure the server boots!
SECRET_V3_SCRIPT = """
print("---------------------------------------")
print("SONIX CLOUD: CONNECTION LIVE!")
print("---------------------------------------")
"""

@app.route('/')
def home():
    return "Sonix Server is Online", 200

@app.route('/load_sonix', methods=['GET'])
def load_sonix():
    return SECRET_V3_SCRIPT, 200

if __name__ == '__main__':
    # Render needs port 10000
    app.run(host='0.0.0.0', port=10000)
