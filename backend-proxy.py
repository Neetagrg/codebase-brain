#!/usr/bin/env python3
"""
Secure Backend Proxy for watsonx.ai
This keeps your API key safe on the server - NEVER exposed to the browser
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Load credentials from environment variables (SECURE)
WATSONX_API_KEY = os.getenv('WATSONX_API_KEY')
WATSONX_PROJECT_ID = os.getenv('WATSONX_PROJECT_ID')
WATSONX_ENDPOINT = os.getenv('WATSONX_ENDPOINT')
WATSONX_MODEL = os.getenv('WATSONX_MODEL', 'ibm/granite-13b-chat-v2')

# Validate credentials are loaded
if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
    raise ValueError("Missing WATSONX_API_KEY or WATSONX_PROJECT_ID in .env file")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'watsonx-proxy',
        'model': WATSONX_MODEL
    })

@app.route('/api/query', methods=['POST'])
def query_watsonx():
    """
    Proxy endpoint for watsonx.ai queries
    Accepts: { "prompt": "your question here", "max_tokens": 2048, "temperature": 0.7 }
    """
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing prompt in request'}), 400
        
        prompt = data['prompt']
        max_tokens = data.get('max_tokens', 2048)
        temperature = data.get('temperature', 0.7)
        
        # Prepare watsonx.ai request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {WATSONX_API_KEY}'
        }
        
        payload = {
            'model_id': WATSONX_MODEL,
            'project_id': WATSONX_PROJECT_ID,
            'input': prompt,
            'parameters': {
                'max_new_tokens': max_tokens,
                'temperature': temperature,
                'top_p': 0.9,
                'top_k': 50
            }
        }
        
        # Make request to watsonx.ai
        response = requests.post(
            WATSONX_ENDPOINT,
            headers=headers,
            json=payload,
            stream=True
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': 'watsonx.ai API error',
                'status_code': response.status_code,
                'message': response.text
            }), response.status_code
        
        # Stream response back to client
        def generate():
            for line in response.iter_lines():
                if line:
                    yield line + b'\n'
        
        return Response(generate(), mimetype='text/event-stream')
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/query-simple', methods=['POST'])
def query_watsonx_simple():
    """
    Simple non-streaming endpoint for watsonx.ai queries
    Accepts: { "prompt": "your question here" }
    Returns: { "response": "AI response here", "tokens_used": 123 }
    """
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing prompt in request'}), 400
        
        prompt = data['prompt']
        max_tokens = data.get('max_tokens', 2048)
        temperature = data.get('temperature', 0.7)
        
        # Prepare watsonx.ai request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {WATSONX_API_KEY}'
        }
        
        # Use non-streaming endpoint
        endpoint = WATSONX_ENDPOINT.replace('_stream', '')
        
        payload = {
            'model_id': WATSONX_MODEL,
            'project_id': WATSONX_PROJECT_ID,
            'input': prompt,
            'parameters': {
                'max_new_tokens': max_tokens,
                'temperature': temperature,
                'top_p': 0.9,
                'top_k': 50
            }
        }
        
        # Make request to watsonx.ai
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': 'watsonx.ai API error',
                'status_code': response.status_code,
                'message': response.text
            }), response.status_code
        
        result = response.json()
        
        # Extract response text and token count
        generated_text = result.get('results', [{}])[0].get('generated_text', '')
        token_count = result.get('results', [{}])[0].get('generated_token_count', 0)
        
        return jsonify({
            'response': generated_text,
            'tokens_used': token_count,
            'model': WATSONX_MODEL
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🔒 Secure watsonx.ai Backend Proxy Server")
    print("=" * 60)
    print(f"✓ API Key loaded: {WATSONX_API_KEY[:20]}...")
    print(f"✓ Project ID: {WATSONX_PROJECT_ID}")
    print(f"✓ Model: {WATSONX_MODEL}")
    print(f"✓ Endpoint: {WATSONX_ENDPOINT}")
    print("=" * 60)
    print("🚀 Starting server on http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

# Made with Bob
