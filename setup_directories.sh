#!/bin/bash

echo "📁 Setting up directories for Offline Gemma..."

# Create necessary directories
mkdir -p uploads
mkdir -p models
mkdir -p offload
mkdir -p scripts

# Set proper permissions
chmod 755 uploads
chmod 755 models
chmod 755 offload
chmod 755 scripts

# Create .gitkeep files to ensure directories are tracked
touch uploads/.gitkeep
touch models/.gitkeep
touch offload/.gitkeep

echo "✅ Directories created:"
echo "   📁 uploads/ - for file uploads"
echo "   📁 models/ - for AI models"
echo "   📁 offload/ - for model offloading"
echo "   📁 scripts/ - for utility scripts"

echo ""
echo "🔧 Checking Docker volume mounts..."
echo "   The following directories are mounted in Docker:"
echo "   - $(pwd)/uploads → /workspace/uploads"
echo "   - $(pwd)/models → /workspace/models"
echo "   - $(pwd)/offload → /workspace/offload"
echo "   - $(pwd)/scripts → /workspace/scripts"

echo ""
echo "🎯 Ready for Docker deployment!" 