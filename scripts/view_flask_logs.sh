#!/bin/bash
echo "🌐 Viewing Flask App Logs (port 5050)..."
echo "Press Ctrl+C to exit"
echo ""

sudo docker logs -f offline-gemma-jetson | grep -E "(5050|Flask|app.py|POST|GET|upload|analyze-media|Starting video analysis|Video saved)" 