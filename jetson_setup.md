# Jetson Nano Setup Guide for Gemma 3n Medical Triage

## Overview

This guide covers setting up the fine-tuned Gemma 3n model on NVIDIA Jetson Nano for medical triage and multimodal AI tasks.

## Quick Start

1. **Download the 4B model** (recommended for Jetson Nano):
   ```bash
   python3 scripts/download_gemma_models.py --model 4b --check-space
   ```

2. **Run the web interface**:
   ```bash
   python3 app.py --model-path ./models/gemma3n-4b
   ```

3. **For better performance**, download both models and use load monitoring:
   ```bash
   python3 scripts/download_gemma_models.py --model both --check-space
   python3 scripts/jetson_load_monitor.py
   ```

## Hardware Requirements

- **Jetson Nano Developer Kit** (4GB RAM model)
- **MicroSD Card**: 32GB+ Class 10 (64GB recommended)
- **Power Supply**: 5V/4A barrel jack
- **USB Audio Interface** (optional, for better audio input)

## System Setup

### 1. Flash JetPack OS
```bash
# Download JetPack 4.6.3 or later
# Flash using NVIDIA SDK Manager
# Enable all components including CUDA, cuDNN, TensorRT
```

### 2. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-dev python3-venv
sudo apt install libopenblas-dev liblapack-dev

# Install audio dependencies
sudo apt install ffmpeg portaudio19-dev python3-pyaudio

# Install PyTorch for Jetson
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install transformers and quantization libraries
pip3 install transformers accelerate bitsandbytes
pip3 install soundfile librosa
```

## Model Download and Setup

### Install Pytorch and Dependencies with docker
nvcr.io/nvidia/l4t-pytorch:r35.1.0-pth1.11-py3
dustynv/transformers:r35.1.1.

### 1. Download Gemma 3n Models

The project includes a convenient script to download Gemma 3n models. For Jetson Nano, we recommend starting with the 4B model for better performance:

```bash
# Clone your repository
git clone <your-repo>
cd offline-gemma

# Download the 4B model first (recommended for Jetson Nano)
python3 scripts/download_gemma_models.py --model 4b

# Check disk space before downloading (optional)
python3 scripts/download_gemma_models.py --model 4b --check-space

# Download both models if you have enough space
python3 scripts/download_gemma_models.py --model both --check-space
```

### 2. Model Options

The downloader supports two model sizes:

- **4B Model** (`cherchercher020/gemma-3N-finetune-100-injury-images`): ~8GB
  - Better performance and quality
  - Recommended for Jetson Nano with 4GB RAM
  - Includes injury detection capabilities

- **2B Model** (`google/gemma-3n-E2B-it`): ~4GB
  - Smaller and faster
  - Good for quick tasks
  - Basic multimodal capabilities

### 3. Download Commands

```bash
# Download 4B model (recommended)
python3 scripts/download_gemma_models.py --model 4b

# Download 2B model
python3 scripts/download_gemma_models.py --model 2b

# Download both models
python3 scripts/download_gemma_models.py --model both

# Check disk space before downloading
python3 scripts/download_gemma_models.py --model 4b --check-space

# Test model loading after download
python3 scripts/download_gemma_models.py --model 4b --test-load
```

### 4. Model Fine-tuning Details

The models are fine-tuned specifically for medical triage applications:

- **4B Model**: Fine-tuned on 100 injury images for medical assessment
- **2B Model**: Base Gemma 3n model with multimodal capabilities
- **Medical capabilities**: Injury detection, wound assessment, triage recommendations

## Performance Expectations

### Model Comparison

| Model | Size | RAM Usage | Speed | Quality | Use Case |
|-------|------|-----------|-------|---------|----------|
| 4B Model | ~8GB | ~3.5GB | Medium | High | Primary use |
| 2B Model | ~4GB | ~2.5GB | Fast | Good | Quick tasks |

### Memory Usage
- **4B Model loading**: ~3.5GB RAM
- **2B Model loading**: ~2.5GB RAM
- **Audio processing**: ~500MB additional
- **Total peak (4B)**: ~4GB (within 4GB limit with optimization)

### Speed Performance
- **Model loading**: 30-90 seconds (4B), 20-60 seconds (2B)
- **Audio transcription**: 2-5 seconds per token (4B), 1-3 seconds per token (2B)
- **30-second audio**: 30-90 seconds total processing time

### Quality Impact
- **4B Model**: Best quality, injury detection capabilities
- **2B Model**: Good quality, basic multimodal capabilities
- **Audio transcription**: Maintains good accuracy on both models

## Usage Examples

### 1. Basic Medical Triage
```python
from jetson_gemma_runner import JetsonGemmaRunner

# Initialize runner
runner = JetsonGemmaRunner("./models/gemma3n-4b")

# Analyze injury image
result = runner.analyze_injury("injury_photo.jpg")
print(f"Triage assessment: {result}")
```

### 2. Web Interface
```bash
# Run the Flask app with 4B model
python3 app.py --model-path ./models/gemma3n-4b

# Run with 2B model for faster performance
python3 app.py --model-path ./models/gemma3n-2b
```

### 3. Dual Model Setup (Advanced)

For optimal performance, you can use both models with automatic switching:

```bash
# Run load monitoring to automatically choose the best model
python3 scripts/jetson_load_monitor.py

# This will automatically switch between 2B and 4B models based on:
# - System load
# - Available memory
# - Task complexity
```

## Optimization Tips

### 1. Memory Management
```python
# Use aggressive garbage collection
import gc
gc.collect()

# Limit concurrent operations
torch.set_num_threads(4)  # Use all 4 cores
```

### 2. Image Processing
```python
# Use standard image formats (JPEG, PNG)
# Ensure good lighting for injury photos
# Use high resolution for detailed assessment
```

### 3. System Tuning
```bash
# Disable GUI to save memory
sudo systemctl set-default multi-user.target

# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Troubleshooting

### Common Issues

1. **Out of Memory Errors**
   - Close other applications
   - Increase swap space
   - Use 2B model for lower memory usage

2. **Slow Performance**
   - Check CPU usage with `htop`
   - Ensure proper cooling (Jetson Nano throttles when hot)
   - Use 2B model for faster processing

3. **Image Processing Issues**
   - Ensure good lighting for injury photos
   - Use high resolution images for detailed assessment
   - Check image format compatibility (JPEG, PNG)

### Performance Monitoring
```bash
# Monitor system resources
htop
nvidia-smi  # GPU usage
free -h     # Memory usage
df -h       # Disk usage
```

## Use Cases for Jetson Nano

### 1. Medical Triage and Assessment
- **Emergency response**: Injury assessment in field
- **Remote medicine**: Wound evaluation
- **First aid**: Triage recommendations

### 2. Edge AI Applications
- **Privacy**: No internet required
- **Latency**: Local processing
- **Reliability**: Works without cloud connectivity

### 3. Medical IoT Integration
- **Field hospitals**: Portable injury assessment
- **Ambulance systems**: Real-time triage
- **Rural healthcare**: Offline medical assistance

## Comparison with Other Devices

| Device | RAM | Model Size | Speed | Cost |
|--------|-----|------------|-------|------|
| Jetson Nano | 4GB | 3GB | Slow | $99 |
| Jetson Xavier NX | 8GB | 3GB | Fast | $399 |
| Desktop (8GB) | 8GB | 11GB | Fast | $500+ |
| Cloud GPU | 16GB+ | 11GB | Very Fast | $1-5/hr |

## Conclusion

The quantized Gemma 3n model is well-suited for Jetson Nano deployment, offering:
- ✅ **Feasible memory usage** (2.5GB RAM)
- ✅ **Good quality retention** (1-2% degradation)
- ✅ **Offline operation** (no internet required)
- ⚠️ **Slow performance** (2-5s per token)
- ⚠️ **Limited concurrent users** (single user recommended)

For production use cases requiring faster performance, consider Jetson Xavier NX or cloud deployment. 


### Extras
screen recording in jetson: gst-launch-1.0 ximagesrc num-buffers=100 use-damage=0 ! video/x-raw ! nvvidconv ! 'video/x-raw(memory:NVMM),format=NV12' ! nvv4l2h264enc ! h264parse ! qtmux ! filesink location=a.mp4