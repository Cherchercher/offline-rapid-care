#!/bin/bash

echo "🚀 Starting All RapidCare Services in Docker Container..."

# Check if container is running
if ! docker ps | grep -q offline-gemma-jetson; then
    echo "❌ Container is not running. Start it first with ./build_and_run.sh"
    exit 1
fi

echo "📡 Starting Uploads Server (port 11435)..."
docker exec -d offline-gemma-jetson python3 serve_uploads.py

echo "🤖 Starting Model API Server (port 5001)..."
docker exec -d offline-gemma-jetson python3 model_server.py

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Check all services
echo "🔍 Checking service status..."

# Check uploads server
if curl -s http://localhost:11435 > /dev/null 2>&1; then
    echo "✅ Uploads Server: http://localhost:11435"
else
    echo "⚠️  Uploads Server: Still starting up..."
fi

# Check model API server
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "✅ Model API Server: http://localhost:5001"
else
    echo "⚠️  Model API Server: Still starting up..."
fi

# Check Flask app
if curl -s http://localhost:5050 > /dev/null 2>&1; then
    echo "✅ Flask App: http://localhost:5050"
else
    echo "⚠️  Flask App: Still starting up..."
fi

echo ""
echo "🎯 All services should now be running:"
echo "   📱 Flask App: http://localhost:5050"
echo "   🤖 Model API: http://localhost:5001"
echo "   📁 Uploads: http://localhost:11435"
echo ""
echo "🔍 Check logs with: docker logs offline-gemma-jetson"
echo "🛑 Stop all with: docker stop offline-gemma-jetson" 