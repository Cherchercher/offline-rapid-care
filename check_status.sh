#!/bin/bash

# Check application status and health
echo "🔍 Checking Offline Gemma Application Status"
echo "============================================"

# Check if container is running
echo "📊 Container Status:"
if docker ps | grep -q offline-gemma-jetson; then
    echo "✅ Container is running"
    docker ps | grep offline-gemma-jetson
else
    echo "❌ Container is not running"
    echo "📋 Recent container logs:"
    docker logs offline-gemma-jetson --tail 20
    exit 1
fi

echo ""

# Check container health
echo "🏥 Container Health:"
if docker inspect offline-gemma-jetson | grep -q '"Status": "healthy"'; then
    echo "✅ Container is healthy"
else
    echo "⚠️  Container health status unknown"
fi

echo ""

# Check if models are downloaded
echo "📁 Model Status:"
if [ -d "models/gemma3n-4b" ]; then
    echo "✅ 4B model exists"
    ls -la models/gemma3n-4b/ | head -5
else
    echo "❌ 4B model not found"
fi

if [ -d "models/gemma3n-2b" ]; then
    echo "✅ 2B model exists"
else
    echo "ℹ️  2B model not downloaded (optional)"
fi

echo ""

# Test web interface
echo "🌐 Web Interface Test:"
if curl -s -f http://localhost:5050/api/status > /dev/null; then
    echo "✅ Web interface is responding"
    echo "   🌐 Access at: http://localhost:5050"
else
    echo "❌ Web interface not responding"
    echo "   📋 Checking container logs..."
    docker logs offline-gemma-jetson --tail 10
fi

echo ""

# Check system resources
echo "💻 System Resources:"
echo "   CPU/Memory usage:"
docker stats offline-gemma-jetson --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""

# Check GPU usage (if available)
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 GPU Status:"
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits
else
    echo "ℹ️  nvidia-smi not available"
fi

echo ""

# Show recent logs
echo "📋 Recent Application Logs:"
docker logs offline-gemma-jetson --tail 10

echo ""
echo "🎯 Quick Actions:"
echo "   📊 Monitor logs: docker logs -f offline-gemma-jetson"
echo "   🛑 Stop app: docker stop offline-gemma-jetson"
echo "   🔄 Restart: docker restart offline-gemma-jetson"
echo "   🌐 Open browser: http://localhost:5050" 