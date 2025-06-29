#!/usr/bin/env python3
"""
Test script for RapidCare setup
This script verifies that all components are working correctly
"""

import os
import sys
import json
import requests
from datetime import datetime

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        import transformers
        print(f"✅ Transformers: {transformers.__version__}")
    except ImportError as e:
        print(f"❌ Transformers import failed: {e}")
        return False
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import flask
        print(f"✅ Flask: {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        from model_manager import ModelManager
        print("✅ Model Manager imported successfully")
    except ImportError as e:
        print(f"❌ Model Manager import failed: {e}")
        return False
    
    try:
        from video_processor import VideoProcessor
        print("✅ Video Processor imported successfully")
    except ImportError as e:
        print(f"❌ Video Processor import failed: {e}")
        return False
    
    return True

def test_model_manager():
    """Test model manager functionality"""
    print("\n🧠 Testing Model Manager...")
    
    try:
        from model_manager import ModelManager
        
        # Test auto mode
        print("Testing auto mode...")
        mm = ModelManager(mode="auto")
        status = mm.get_status()
        print(f"✅ Model Manager initialized in {status['mode']} mode")
        
        # Test chat functionality
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, this is a test message."}
        ]
        
        result = mm.chat(messages)
        if result['success']:
            print("✅ Chat functionality working")
            print(f"   Response: {result['response'][:100]}...")
        else:
            print(f"❌ Chat failed: {result.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Model Manager test failed: {e}")
        return False

def test_video_processor():
    """Test video processor functionality"""
    print("\n🎥 Testing Video Processor...")
    
    try:
        from video_processor import VideoProcessor
        
        # Initialize video processor
        vp = VideoProcessor()
        status = vp.get_status()
        print(f"✅ Video Processor initialized")
        print(f"   Frame interval: {status['frame_interval']}")
        print(f"   Max frames: {status['max_frames']}")
        print(f"   Image size: {status['image_size']}")
        
        # Test with a dummy frame
        import numpy as np
        dummy_frame = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
        
        analysis = vp.analyze_frame(dummy_frame, "PARAMEDIC")
        if 'error' not in analysis:
            print("✅ Frame analysis working")
            print(f"   Triage level: {analysis.get('triage_level', 'Unknown')}")
        else:
            print(f"❌ Frame analysis failed: {analysis.get('error', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Video Processor test failed: {e}")
        return False

def test_ollama_connection():
    """Test Ollama connection"""
    print("\n🔗 Testing Ollama Connection...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama connected successfully")
            print(f"   Available models: {len(models)}")
            
            # Check for Gemma model
            gemma_models = [m for m in models if 'gemma' in m.get('name', '').lower()]
            if gemma_models:
                print(f"   Gemma models found: {[m['name'] for m in gemma_models]}")
            else:
                print("   ⚠️  No Gemma models found")
            
            return True
        else:
            print(f"❌ Ollama connection failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

def test_flask_app():
    """Test Flask app endpoints"""
    print("\n🌐 Testing Flask App...")
    
    try:
        # Import and test app
        from app import app
        
        with app.test_client() as client:
            # Test status endpoint
            response = client.get('/api/status')
            if response.status_code == 200:
                print("✅ Status endpoint working")
                data = response.get_json()
                print(f"   Model mode: {data.get('model_status', {}).get('mode', 'Unknown')}")
            else:
                print(f"❌ Status endpoint failed: {response.status_code}")
                return False
            
            # Test roles endpoint
            response = client.get('/api/roles')
            if response.status_code == 200:
                print("✅ Roles endpoint working")
                data = response.get_json()
                print(f"   Available roles: {len(data)}")
            else:
                print(f"❌ Roles endpoint failed: {response.status_code}")
                return False
            
            # Test chat endpoint
            chat_data = {
                'message': 'Test message',
                'role': 'PARAMEDIC'
            }
            response = client.post('/api/chat', json=chat_data)
            if response.status_code == 200:
                print("✅ Chat endpoint working")
            else:
                print(f"❌ Chat endpoint failed: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def test_file_structure():
    """Test that required files and directories exist"""
    print("\n📁 Testing File Structure...")
    
    required_files = [
        'app.py',
        'model_manager.py',
        'video_processor.py',
        'requirements.txt',
        'start.sh',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js',
        'static/js/sw.js',
        'static/manifest.json'
    ]
    
    required_dirs = [
        'templates',
        'static',
        'static/css',
        'static/js',
        'static/images'
    ]
    
    all_good = True
    
    # Check directories
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ Directory: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            all_good = False
    
    # Check files
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ File: {file_path}")
        else:
            print(f"❌ Missing file: {file_path}")
            all_good = False
    
    return all_good

def main():
    """Run all tests"""
    print("🚑 RapidCare Setup Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Ollama Connection", test_ollama_connection),
        ("Model Manager", test_model_manager),
        ("Video Processor", test_video_processor),
        ("Flask App", test_flask_app)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Run: ./start.sh")
        print("2. Open: http://localhost:5000")
        print("3. Test the PWA functionality")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Check setup_guide.md for detailed instructions")
        print("2. Ensure all dependencies are installed")
        print("3. Verify Ollama is running (if using Ollama mode)")
        print("4. Check system resources (RAM, GPU)")

if __name__ == "__main__":
    main() 