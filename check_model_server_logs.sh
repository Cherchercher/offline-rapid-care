#!/bin/bash
echo "🔍 Checking Model Server (port 5001) Logs..."
echo ""

echo "📋 Checking if model server is running:"
sudo docker exec offline-gemma-jetson ps aux | grep model_server

echo ""
echo "🌐 Checking model server health:"
curl -s http://localhost:5001/health || echo "❌ Model server not responding"

echo ""
echo "📨 Recent model server logs:"
sudo docker logs offline-gemma-jetson 2>&1 | grep -E "(model_server|5001|chat/video)" | tail -20

echo ""
echo "🎬 Video processing logs:"
sudo docker logs offline-gemma-jetson 2>&1 | grep -E "(video|Video|frame|Frame|tmp|TMP)" | tail -10

echo ""
echo "❌ Model server errors:"
sudo docker logs offline-gemma-jetson 2>&1 | grep -E "(Error|error|Exception|exception)" | tail -10

echo ""
echo "🔍 Testing model server directly:"
sudo docker exec offline-gemma-jetson python3 -c "
import requests
try:
    response = requests.get('http://localhost:5001/health', timeout=5)
    print(f'Model server health: {response.status_code}')
    print(f'Response: {response.json()}')
except Exception as e:
    print(f'Model server error: {e}')
" 