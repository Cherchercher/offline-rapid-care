#!/bin/bash

# Model Download Script for Offline Gemma
# Downloads the finetuned 4B model with injury detection capabilities

set -e

echo "📥 Offline Gemma Model Downloader"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Create models directory
mkdir -p models

# Check which models to download
echo "🎯 Available models:"
echo "   1. 4B Finetuned (Recommended) - Injury detection model (~8GB)"
echo "   2. 2B Base - Standard model (~4GB)"
echo "   3. Both models (~12GB)"

read -p "Which model(s) would you like to download? (1/2/3): " choice

case $choice in
    1)
        echo "📥 Downloading 4B finetuned model..."
        MODEL_CHOICE="4b"
        ;;
    2)
        echo "📥 Downloading 2B base model..."
        MODEL_CHOICE="2b"
        ;;
    3)
        echo "📥 Downloading both models..."
        MODEL_CHOICE="both"
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

# Check if transformers is available
if python3 -c "import transformers" 2>/dev/null; then
    echo "✅ Transformers library available. Proceeding with download..."
    python3 scripts/download_gemma_models.py --model $MODEL_CHOICE --check-space
else
    echo "⚠️  Transformers not available. Installing required packages..."
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3 is not available. Please install pip3 first."
        exit 1
    fi
    
    # Install required packages
    echo "📦 Installing required packages..."
    pip3 install transformers huggingface_hub torch
    
    # Download models
    echo "📥 Downloading models..."
    python3 scripts/download_gemma_models.py --model $MODEL_CHOICE --check-space
fi

echo ""
echo "✅ Model download completed!"
echo "📁 Models are stored in: ./models/"
echo ""
echo "🎯 Next steps:"
echo "   1. Run the Docker container: ./build_and_run.sh"
echo "   2. Or run directly: python3 app.py"
echo ""
echo "📊 Model information:"
if [ -d "models/gemma3n-4b" ]; then
    echo "   ✅ 4B Finetuned model: Injury detection capabilities"
fi
if [ -d "models/gemma3n-2b" ]; then
    echo "   ✅ 2B Base model: Standard multimodal capabilities"
fi 