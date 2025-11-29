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

@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    try:
        from database import get_dashboard_stats
        stats = get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/products', methods=['POST'])
def add_new_product():
    try:
        from database import add_product
        product = request.json
        
        # Basic validation
        if not product.get('sku') or not product.get('name') or not product.get('base_cost'):
            return jsonify({"error": "Missing required fields"}), 400
            
        success = add_product(product)
        if success:
            return jsonify({"message": "Product added successfully"}), 201
        else:
            return jsonify({"error": "SKU already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting RFP Automation Server on port 5000...")
    # Initialize Database
    from database import initialize_db
    initialize_db()
    
    # Run on 0.0.0.0 to ensure it's accessible from localhost/127.0.0.1
    app.run(host='0.0.0.0', debug=True, port=5000)
