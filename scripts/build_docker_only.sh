#!/bin/bash

# Build Docker image only (no local model download)
echo "🔨 Building Docker image for Jetson Xavier..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p models uploads offload
touch uploads/.gitkeep models/.gitkeep offload/.gitkeep

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t offline-gemma-jetson .

echo "✅ Docker image built successfully!"
echo ""
echo "🎯 Next steps:"
echo "   1. Download models: ./download_models_docker.sh"
echo "   2. Or run with model download: ./build_and_run.sh"
echo "   3. Or use docker-compose: docker-compose up -d" 