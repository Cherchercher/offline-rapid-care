#!/bin/bash
echo "📊 Viewing All Service Logs with Color Coding..."
echo "Press Ctrl+C to exit"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

sudo docker logs -f offline-gemma-jetson | while read line; do
    if echo "$line" | grep -q "5001\|model_server\|chat/"; then
        echo -e "${BLUE}[MODEL]${NC} $line"
    elif echo "$line" | grep -q "5050\|Flask\|app.py"; then
        echo -e "${GREEN}[FLASK]${NC} $line"
    elif echo "$line" | grep -q "11435\|uploads\|serve_uploads"; then
        echo -e "${YELLOW}[UPLOAD]${NC} $line"
    elif echo "$line" | grep -q "Error\|error\|Exception\|exception"; then
        echo -e "${RED}[ERROR]${NC} $line"
    else
        echo "$line"
    fi
done 