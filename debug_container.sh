#!/bin/bash

# Debug script to check container issues
echo "🔍 Debugging Container Issues"
echo "============================="

# Check if container exists
echo "📊 Container Status:"
if docker ps -a | grep -q offline-gemma-jetson; then
    echo "✅ Container exists"
    docker ps -a | grep offline-gemma-jetson
else
    echo "❌ Container doesn't exist"
fi

echo ""

# Check container logs
echo "📋 Container Logs (last 50 lines):"
docker logs offline-gemma-jetson --tail 50

echo ""

# Check if container is running
echo "🔄 Container State:"
if docker ps | grep -q offline-gemma-jetson; then
    echo "✅ Container is running"
else
    echo "❌ Container is not running"
    echo "   Exit code: $(docker inspect offline-gemma-jetson --format='{{.State.ExitCode}}')"
fi

echo ""

# Check disk space
echo "💾 Disk Space:"
df -h .

echo ""

# Check models directory
echo "📁 Models Directory:"
ls -la models/ 2>/dev/null || echo "Models directory doesn't exist"

echo ""

# Try to run container interactively for debugging
echo "🔧 Interactive Debug Mode:"
echo "   This will start the container interactively to see what's happening..."
echo "   Press Ctrl+C to exit debug mode"
echo ""

read -p "Start interactive debug? (y/n): " debug_choice

if [ "$debug_choice" = "y" ]; then
    echo "🚀 Starting interactive container..."
    docker run -it --rm \
        --name debug-offline-gemma \
        --runtime=nvidia \
        --gpus all \
        -v $(pwd)/models:/workspace/models \
        -v $(pwd)/scripts:/workspace/scripts \
        offline-gemma-jetson \
        /bin/bash
fi 