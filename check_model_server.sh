#!/bin/bash

echo "🔍 Checking Model API Server (port 5001)..."

# Check if container is running
if ! docker ps | grep -q offline-gemma-jetson; then
    echo "❌ Container is not running"
    exit 1
fi

echo "📊 Container processes:"
docker exec offline-gemma-jetson ps aux | grep -E "(model_server|python)" || echo "No model_server processes found"

echo ""
echo "🌐 Health check:"
curl -s http://localhost:5001/health || echo "❌ Health check failed"

echo ""
echo "📋 Recent container logs (last 50 lines):"
docker logs --tail 50 offline-gemma-jetson

echo ""
echo "🔍 Model server specific logs:"
docker exec offline-gemma-jetson python3 -c "
import requests
try:
    response = requests.get('http://localhost:5001/status', timeout=5)
    print(f'Model server status: {response.json()}')
except Exception as e:
    print(f'Model server error: {e}')
"

echo ""
echo "💾 Memory usage:"
docker exec offline-gemma-jetson free -h

echo ""
echo "🔥 GPU usage:"
docker exec offline-gemma-jetson nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits 2>/dev/null || echo "GPU info not available" 