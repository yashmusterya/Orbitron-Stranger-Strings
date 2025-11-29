from flask import Flask, request, jsonify
from flask_cors import CORS
from rfp_system import Orchestrator
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) # Allow all origins explicitly

orchestrator = Orchestrator()

@app.route('/api/process-rfp', methods=['POST'])
def process_rfp():
    data = request.json
    input_text = data.get('input')
    
    if not input_text:
        return jsonify({"error": "No input provided"}), 400
    
    print(f"Received request: {input_text}")
    
    try:
        # Run the full workflow
        result = orchestrator.run(input_text)
        return jsonify(result)

    except Exception as e:
        print(f"Error processing RFP: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting RFP Automation Server on port 5000...")
    # Run on 0.0.0.0 to ensure it's accessible from localhost/127.0.0.1
    app.run(host='0.0.0.0', debug=True, port=5000)
