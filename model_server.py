#!/usr/bin/env python3
"""
Model API Server for Gemma 3n
This server provides a REST API for the Gemma model, allowing the Flask app to use it without loading the model twice.
"""

from flask import Flask, request, jsonify
from model_manager_pipeline import get_pipeline_manager
import json
import time

app = Flask(__name__)

# Initialize model manager (this will load the model once)
print("🚀 Starting Model API Server...")
model_manager = get_pipeline_manager()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': True,
        'timestamp': time.time()
    })

@app.route('/chat/text', methods=['POST'])
def chat_text():
    """Text-only chat endpoint"""
    try:
        data = request.json
        messages = data.get('messages', [])
        
        print(f"📨 Received text chat request with {len(messages)} messages")
        
        # Use model manager for text-only request
        print(f"📤 Sending text request to model manager...")
        result = model_manager.chat_text(messages)
        print(f"📥 Received text result from model manager: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in text chat endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/chat/image', methods=['POST'])
def chat_image():
    """Image analysis endpoint"""
    try:
        data = request.json
        messages = data.get('messages', [])
        
        print(f"📨 Received image chat request with {len(messages)} messages")
        
        # Use model manager for image request
        print(f"📤 Sending image request to model manager...")
        result = model_manager.chat_image(messages)
        print(f"📥 Received image result from model manager: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in image chat endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/chat/video', methods=['POST'])
def chat_video():
    """Video analysis endpoint"""
    try:
        data = request.json
        messages = data.get('messages', [])
        
        print(f"📨 Received video chat request with {len(messages)} messages")
        
        # Use model manager for video request
        print(f"📤 Sending video request to model manager...")
        result = model_manager.chat_video(messages)
        print(f"📥 Received video result from model manager: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in video chat endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/chat/audio', methods=['POST'])
def chat_audio():
    """Audio transcription endpoint"""
    try:
        data = request.json
        messages = data.get('messages', [])
        
        print(f"📨 Received audio chat request with {len(messages)} messages")
        
        # Use model manager for audio request
        print(f"📤 Sending audio request to model manager...")
        result = model_manager.chat_audio(messages)
        print(f"📥 Received audio result from model manager: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in audio chat endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/status', methods=['GET'])
def status():
    """Get model status"""
    return jsonify({
        'success': True,
        'status': model_manager.get_status(),
        'timestamp': time.time()
    })

@app.route('/test-text', methods=['POST'])
def test_text():
    """Test endpoint for text-only requests"""
    try:
        data = request.json
        test_message = data.get('message', 'Hello, how are you?')
        
        print(f"🧪 Testing text-only request: {test_message}")
        
        # Simple text-only messages
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": test_message}
                ]
            }
        ]
        
        # Use model manager to get response
        print(f"📤 Sending text test to model manager...")
        result = model_manager.chat_text(messages)
        print(f"📥 Received text test result: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in text test: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🔧 Model API Server ready on port 5001")
    print("📊 Health check: http://localhost:5001/health")
    print("💬 Chat endpoint: http://localhost:5001/chat")
    app.run(host='0.0.0.0', port=5001, debug=False) 