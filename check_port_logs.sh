#!/bin/bash
echo "🔍 Checking logs from port 5001 (Model Server)..."
echo ""

# Check if port 5001 is listening
echo "📡 Port 5001 status:"
netstat -tulpn | grep :5001 || echo "❌ Port 5001 not listening"

echo ""
echo "📋 Recent logs from model server:"
sudo docker logs offline-gemma-jetson 2>&1 | grep "5001\|model_server\|chat/video" | tail -20

echo ""
echo "🎬 Video processing logs:"
sudo docker logs offline-gemma-jetson 2>&1 | grep -i "video\|frame\|tmp" | tail -10 