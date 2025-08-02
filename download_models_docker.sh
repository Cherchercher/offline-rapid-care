#!/bin/bash

# Download models inside Docker container where environment is correct
echo "📥 Downloading models inside Docker container..."

# Build the image first
echo "🔨 Building Docker image..."
docker build -t offline-gemma-jetson .

# Create a temporary container to download models
echo "📦 Creating temporary container for model download..."
docker run --rm \
    --name temp-model-download \
    -v $(pwd)/models:/workspace/models \
    -v $(pwd)/scripts:/workspace/scripts \
    offline-gemma-jetson \
    python3 /workspace/scripts/download_gemma_models.py --model 4b --check-space

echo "✅ Models downloaded successfully!"
echo "📁 Models are now in: ./models/" 