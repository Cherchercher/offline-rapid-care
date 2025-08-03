#!/bin/bash
echo "📁 Viewing Upload Server Logs (port 11435)..."
echo "Press Ctrl+C to exit"
echo ""

sudo docker logs -f offline-gemma-jetson | grep -E "(11435|uploads|serve_uploads|file|upload)" 