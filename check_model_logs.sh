#!/bin/bash
echo "🔍 Checking Model Server Logs..."
echo ""

echo "📋 Recent container logs (last 50 lines):"
sudo docker logs --tail 50 offline-gemma-jetson

echo ""
echo "🎬 Looking for video processing logs:"
sudo docker logs offline-gemma-jetson | grep -E "(video|Video|frame|Frame|tmp|TMP)" | tail -20

echo ""
echo "📨 Looking for API requests:"
sudo docker logs offline-gemma-jetson | grep -E "(POST|GET|Request|request)" | tail -10

echo ""
echo "❌ Looking for errors:"
sudo docker logs offline-gemma-jetson | grep -E "(Error|error|Exception|exception)" | tail -10 