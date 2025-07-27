#!/usr/bin/env python3
"""
Direct Gemma 3n Server - Uses local model with full audio support
"""

from flask import Flask, request, jsonify
import torch
from transformers import AutoProcessor, Gemma3nForConditionalGeneration
import os
import json
from datetime import datetime
import uuid
from prompts import AUDIO_TRANSCRIPTION_PROMPT

app = Flask(__name__)

# Configuration
MODEL_PATH = "./models/gemma3n-local"
UPLOADS_DIR = "./uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Global model variables
model = None
processor = None

def load_model():
    """Load the Gemma 3n model locally"""
    global model, processor
    
    print("📥 Loading Gemma 3n model from local path...")
    
    try:
        # Load processor and model
        processor = AutoProcessor.from_pretrained(MODEL_PATH)
        model = Gemma3nForConditionalGeneration.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float32,  # Use float32 for CPU
            device_map="cpu",           # Force CPU usage
            low_cpu_mem_usage=True      # Use low CPU memory
        )
        
        print("✅ Model loaded successfully!")
        print("🎯 Full audio, image, and video capabilities available")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise

@app.route('/api/transcribe-audio', methods=['POST'])
def transcribe_audio():
    """Transcribe audio using local Gemma 3n model"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['file']
        prompt = request.form.get('prompt', AUDIO_TRANSCRIPTION_PROMPT)
        
        if file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save uploaded audio
        filename = f"audio_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        audio_path = os.path.join(UPLOADS_DIR, filename)
        file.save(audio_path)
        
        print(f"🔊 Processing audio: {audio_path}")
        
        # Create messages for the model
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "audio", "audio": audio_path},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        # Apply chat template
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt"
        )
        
        # Move to device
        inputs = inputs.to(model.device, dtype=model.dtype)
        
        # Generate response
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.1,
                top_p=0.9
            )
        
        # Decode response
        input_len = inputs["input_ids"].shape[-1]
        response_tokens = outputs[0][input_len:]
        transcription = processor.decode(response_tokens, skip_special_tokens=True)
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'audio_path': audio_path,
            'timestamp': datetime.now().isoformat(),
            'mode': 'direct_python'
        })
        
    except Exception as e:
        print(f"❌ Audio transcription error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with the local Gemma 3n model"""
    try:
        data = request.json
        messages = data.get('messages', [])
        
        # Apply chat template
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt"
        )
        
        # Move to device
        inputs = inputs.to(model.device, dtype=model.dtype)
        
        # Generate response
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7
            )
        
        # Decode response
        input_len = inputs["input_ids"].shape[-1]
        response_tokens = outputs[0][input_len:]
        response = processor.decode(response_tokens, skip_special_tokens=True)
        
        return jsonify({
            'success': True,
            'response': response,
            'mode': 'direct_python'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Get model status"""
    return jsonify({
        'model_loaded': model is not None,
        'model_path': MODEL_PATH,
        'device': str(model.device) if model else None,
        'mode': 'direct_python'
    })

if __name__ == '__main__':
    # Load model on startup
    load_model()
    
    print("🚀 Starting Direct Gemma 3n Server...")
    print("📡 Server will run on http://localhost:5051")
    print("🎯 Full audio, image, and video support available")
    
    app.run(host='0.0.0.0', port=5051, debug=True) 