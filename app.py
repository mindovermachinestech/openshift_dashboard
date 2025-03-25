from flask import Flask, request, jsonify
from openshift_agent import process_request

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    """Chatbot API to interact with the OpenShift agent."""
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({"error": "No message provided."}), 400
    response = process_request(user_input)
    return jsonify({"response": response})

def run_flask_app():
    """Run the Flask application."""
    app.run(host="0.0.0.0", port=5000)
