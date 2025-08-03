#!/bin/bash
echo "🤖 Viewing Model Server Logs (port 5001)..."
echo "Press Ctrl+C to exit"
echo ""

sudo docker logs -f offline-gemma-jetson | grep -E "(5001|model_server|chat/video|chat/image|chat/text|Starting video|No frames|Video path|File exists)" 