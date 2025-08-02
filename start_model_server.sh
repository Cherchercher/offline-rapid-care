#!/bin/bash

echo "🚀 Starting Model API Server inside Docker container..."

# Check if container is running
if ! docker ps | grep -q offline-gemma-jetson; then
    echo "❌ Container is not running. Start it first with ./build_and_run.sh"
    exit 1
fi

# Start model server in background inside container
echo "📡 Starting model server on port 5001..."
docker exec -d offline-gemma-jetson python3 model_server.py

# Wait for server to start
echo "⏳ Waiting for model server to start..."
sleep 10

# Check if server is responding
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "✅ Model API Server is running on http://localhost:5001"
    echo "📊 Health check: http://localhost:5001/health"
    echo "💬 Chat endpoint: http://localhost:5001/chat/text"
else
    echo "⚠️  Model server may still be starting up..."
    echo "🔍 Check logs with: docker logs offline-gemma-jetson"
fi

echo ""
echo "🎯 Now both services are running:"
echo "   📱 Flask App: http://localhost:5050"
echo "   🤖 Model API: http://localhost:5001" 