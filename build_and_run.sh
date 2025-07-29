#!/bin/bash

# Build and Run Script for Offline Gemma on Jetson Xavier
# This script builds the Docker image and runs the container

set -e

echo "🚀 Building and running Offline Gemma for Jetson Xavier..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if NVIDIA Docker runtime is available
if ! docker info | grep -q "nvidia"; then
    echo "⚠️  NVIDIA Docker runtime not detected. GPU acceleration may not work."
    echo "   Make sure you have nvidia-docker2 installed and configured."
fi

# Create necessary directories if they don't exist
echo "📁 Creating necessary directories..."
mkdir -p models uploads offload

# Create .gitkeep files to ensure directories are tracked
touch uploads/.gitkeep
touch models/.gitkeep
touch offload/.gitkeep

# Check if models need to be downloaded
if [ ! -d "models/gemma3n-4b" ]; then
    echo "📥 Models not found. Downloading finetuned 4B model..."
    echo "   This will download the injury detection finetuned model (~8GB)"
    
    # Check if Python and required packages are available
    if command -v python3 &> /dev/null; then
        # Check if transformers is available
        if python3 -c "import transformers" 2>/dev/null; then
            echo "✅ Python and transformers available. Downloading model..."
            python3 scripts/download_gemma_models.py --model 4b --check-space
        else
            echo "⚠️  Transformers not available. Installing in temporary environment..."
            # Create temporary virtual environment for downloading
            python3 -m venv temp_download_env
            source temp_download_env/bin/activate
            pip install transformers huggingface_hub torch
            python3 scripts/download_gemma_models.py --model 4b --check-space
            deactivate
            rm -rf temp_download_env
        fi
    else
        echo "❌ Python3 not available. Please install Python3 and try again."
        exit 1
    fi
else
    echo "✅ Models already exist in models/gemma3n-4b/"
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t offline-gemma-jetson .

# Stop existing container if running
echo "🛑 Stopping existing container if running..."
docker stop offline-gemma-jetson 2>/dev/null || true
docker rm offline-gemma-jetson 2>/dev/null || true

# Run the container
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
    --restart unless-stopped \
    offline-gemma-jetson

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Check container status
echo "📊 Container status:"
docker ps | grep offline-gemma-jetson

# Show logs
echo "📋 Container logs:"
docker logs offline-gemma-jetson

echo ""
echo "✅ Offline Gemma is now running!"
echo "🌐 Access the application at: http://localhost:5050"
echo "📊 Monitor logs with: docker logs -f offline-gemma-jetson"
echo "🛑 Stop with: docker stop offline-gemma-jetson"
echo ""
echo "📁 Model files are stored in: ./models/"
echo "📁 Uploads will be stored in: ./uploads/"
echo "📁 Offload files will be stored in: ./offload/"
echo ""
echo "🎯 The finetuned 4B model with injury detection is ready to use!" 