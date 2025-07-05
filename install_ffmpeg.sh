#!/bin/bash
# Install ffmpeg for audio conversion

echo "Installing ffmpeg..."

# Install ffmpeg
sudo yum install -y ffmpeg ffmpeg-devel

# Check if installation was successful
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg installed successfully"
    ffmpeg -version | head -1
else
    echo "❌ ffmpeg installation failed"
    exit 1
fi 