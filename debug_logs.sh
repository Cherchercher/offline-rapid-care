#!/bin/bash

echo "🔍 Comprehensive Log Debug for Video Processing..."

# Check if container is running
if ! docker ps | grep -q offline-gemma-jetson; then
    echo "❌ Container is not running"
    exit 1
fi

echo ""
echo "📊 1. Container Status:"
docker ps | grep offline-gemma-jetson

echo ""
echo "🐳 2. All Container Logs (last 100 lines):"
docker logs --tail 100 offline-gemma-jetson

echo ""
echo "🔧 3. Running Processes in Container:"
docker exec offline-gemma-jetson ps aux

echo ""
echo "💾 4. Memory Usage:"
docker exec offline-gemma-jetson free -h

echo ""
echo "🔥 5. GPU Status:"
docker exec offline-gemma-jetson nvidia-smi 2>/dev/null || echo "GPU not available"

echo ""
echo "📁 6. Uploads Directory Contents:"
docker exec offline-gemma-jetson ls -la /workspace/uploads/

echo ""
echo "🗄️ 7. Model Directory Contents:"
docker exec offline-gemma-jetson ls -la /workspace/models/

echo ""
echo "🌐 8. Port Listening Status:"
docker exec offline-gemma-jetson netstat -tulpn | grep -E "(5001|5050|11435)" || echo "No ports found"

echo ""
echo "🔍 9. Test Model Server Directly:"
docker exec offline-gemma-jetson python3 -c "
import requests
import time
try:
    print('Testing model server...')
    response = requests.get('http://localhost:5001/health', timeout=5)
    print(f'Health check: {response.status_code}')
    print(f'Response: {response.json()}')
    
    # Test a simple text request
    messages = [{'role': 'user', 'content': [{'type': 'text', 'text': 'Hello'}]}]
    response = requests.post('http://localhost:5001/chat/text', json={'messages': messages}, timeout=30)
    print(f'Text test: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print(f'Success: {result.get(\"success\", False)}')
        print(f'Response: {result.get(\"response\", \"No response\")[:100]}...')
    else:
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Error: {e}')
"

echo ""
echo "📋 10. Recent Flask App Logs (if any):"
docker exec offline-gemma-jetson find /workspace -name "*.log" -exec ls -la {} \; 2>/dev/null || echo "No log files found"

echo ""
echo "🔍 11. Check if model is loaded:"
docker exec offline-gemma-jetson python3 -c "
import torch
import os
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA device count: {torch.cuda.device_count()}')
if torch.cuda.is_available():
    print(f'Current device: {torch.cuda.current_device()}')
    print(f'Device name: {torch.cuda.get_device_name()}')
    print(f'Memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB')
    print(f'Memory cached: {torch.cuda.memory_reserved() / 1024**3:.2f} GB')
print(f'Model directory exists: {os.path.exists(\"/workspace/models/gemma3n-4b\")}')
"

echo ""
echo "�� Debug Complete!" 