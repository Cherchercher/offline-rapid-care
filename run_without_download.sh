#!/bin/bash

# Run container without automatic model download
echo "🚀 Starting Offline Gemma without automatic model download..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p models uploads offload
touch uploads/.gitkeep models/.gitkeep offload/.gitkeep

# Build the Docker image if it doesn't exist
if ! docker images | grep -q offline-gemma-jetson; then
    echo "🔨 Building Docker image..."
    docker build -t offline-gemma-jetson .
fi

# Stop existing container if running
echo "🛑 Stopping existing container if running..."
docker stop offline-gemma-jetson 2>/dev/null || true
docker rm offline-gemma-jetson 2>/dev/null || true

# Run the container without model download
echo "🚀 Starting container..."
docker run -d \
    --name offline-gemma-jetson \
    --runtime=nvidia \
    --gpus all \
    -p 5050:5050 \
    -v $(pwd)/models:/workspace/models \
    -v $(pwd)/uploads:/workspace/uploads \
    -v $(pwd)/rapidcare_offline.db:/workspace/rapidcare_offline.db \
    -v $(pwd)/offload:/workspace/offload \
    -v $(pwd)/scripts:/workspace/scripts \
    --restart unless-stopped \
    offline-gemma-jetson

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Check container status
echo "📊 Container status:"
docker ps | grep offline-gemma-jetson

echo ""
echo "✅ Container is running!"
echo "🌐 Access the application at: http://localhost:5050"
echo ""
echo "📥 To download models later, run:"
echo "   docker exec offline-gemma-jetson python3 /workspace/scripts/download_gemma_models.py --model 4b --check-space"
echo ""
echo "📊 To check status: ./check_status.sh"
echo "🔍 To debug issues: ./debug_container.sh" 