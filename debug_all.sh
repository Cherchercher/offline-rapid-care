#!/bin/bash
echo "🔍 Comprehensive Debug Check..."
echo ""

echo "📊 1. Container Status:"
sudo docker ps | grep offline-gemma-jetson

echo ""
echo "📋 2. All Recent Container Logs (last 100 lines):"
sudo docker logs --tail 100 offline-gemma-jetson

echo ""
echo "🔧 3. Running Processes in Container:"
sudo docker exec offline-gemma-jetson ps aux | grep -E "(python|model|server)"

echo ""
echo "🌐 4. Port Listening Status:"
sudo docker exec offline-gemma-jetson netstat -tulpn | grep -E "(5001|5050|11435)"

echo ""
echo "📁 5. File System Check:"
echo "   /tmp contents:"
sudo docker exec offline-gemma-jetson ls -la /tmp/ | head -10
echo "   /workspace/uploads contents:"
sudo docker exec offline-gemma-jetson ls -la /workspace/uploads/ | head -10

echo ""
echo "❌ 6. Error Logs:"
sudo docker logs offline-gemma-jetson 2>&1 | grep -E "(Error|error|Exception|exception|Failed|failed)" | tail -10

echo ""
echo "🎬 7. Video Processing Logs:"
sudo docker logs offline-gemma-jetson 2>&1 | grep -E "(video|Video|frame|Frame|tmp|TMP)" | tail -10

echo ""
echo "📨 8. API Request Logs:"
sudo docker logs offline-gemma-jetson 2>&1 | grep -E "(POST|GET|Request|request)" | tail -10 