#!/bin/bash

# Quick Start Script for RapidCare
# This is a simplified version for manual startup

echo "🚑 RapidCare Quick Start"
echo "========================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if Ollama is running
echo -e "${BLUE}Checking Ollama...${NC}"
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}Ollama not running. Starting it...${NC}"
    ollama serve > /dev/null 2>&1 &
    sleep 5
fi

# Check if model is available
echo -e "${BLUE}Checking Gemma model...${NC}"
if ! ollama list | grep -q "gemma3n:e4b"; then
    echo -e "${YELLOW}Model not found. Pulling...${NC}"
    ollama pull gemma3n:e4b
fi

# Test model
echo -e "${BLUE}Testing model...${NC}"
response=$(curl -s -X POST http://127.0.0.1:11434/api/chat \
    -H "Content-Type: application/json" \
    -d '{"model": "gemma3n:e4b", "messages": [{"role": "user", "content": "test"}], "stream": false}' \
    --max-time 60 2>/dev/null)

if echo "$response" | grep -q '"message"'; then
    echo -e "${GREEN}✅ Model is ready!${NC}"
else
    echo -e "${YELLOW}⚠️  Model may still be loading. This is normal on first use.${NC}"
fi

# Start Flask app
echo -e "${BLUE}Starting Flask app...${NC}"
echo -e "${GREEN}App will be available at: http://localhost:5050${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

python app.py 