# Jetson Nano Setup Guide for Quantized Gemma 3n

## Overview

This guide covers setting up the quantized Gemma 3n model on NVIDIA Jetson Nano for audio transcription and multimodal AI tasks.

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

## Model Quantization

### 1. Download and Quantize Model
```bash
# Clone your repository
git clone <your-repo>
cd offline-gemma

# Download the full model first (on a machine with more RAM)
python3 download_gemma_local.py

# Quantize the model for Jetson Nano
python3 quantize_model.py
```

### 2. Expected Results
- **Original model**: ~11GB → **Quantized model**: ~3GB
- **Memory usage**: ~10GB → **~2.5GB RAM**
- **Disk space**: ~75% reduction

## Performance Expectations

### Memory Usage
- **Model loading**: ~2.5GB RAM
- **Audio processing**: ~500MB additional
- **Total peak**: ~3.5GB (within 4GB limit)

### Speed Performance
- **Model loading**: 30-60 seconds
- **Audio transcription**: 2-5 seconds per token
- **30-second audio**: 30-60 seconds total processing time

### Quality Impact
- **4-bit quantization**: ~1-2% quality degradation
- **Audio transcription**: Maintains good accuracy
- **Text generation**: Slight reduction in coherence

## Usage Examples

### 1. Basic Audio Transcription
```python
from jetson_gemma_runner import JetsonGemmaRunner

# Initialize runner
runner = JetsonGemmaRunner("./models/gemma3n-local-4bit")

# Transcribe audio file
result = runner.transcribe_audio("sample.wav")
print(f"Transcription: {result}")
```

### 2. Web Interface
```bash
# Run the Flask app with quantized model
python3 app.py --model-path ./models/gemma3n-local-4bit
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

### 2. Audio Processing
```python
# Use smaller audio chunks for long files
# Convert to WAV format for best compatibility
# Use 16kHz sampling rate
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
   - Ensure model is quantized to 4-bit
   - Close other applications
   - Increase swap space

2. **Slow Performance**
   - Check CPU usage with `htop`
   - Ensure proper cooling (Jetson Nano throttles when hot)
   - Use smaller audio files

3. **Audio Issues**
   - Install audio dependencies: `sudo apt install portaudio19-dev`
   - Check audio device permissions
   - Use USB audio interface for better quality

### Performance Monitoring
```bash
# Monitor system resources
htop
nvidia-smi  # GPU usage
free -h     # Memory usage
df -h       # Disk usage
```

## Use Cases for Jetson Nano

### 1. Offline Audio Transcription
- **Emergency response**: Transcribe emergency calls
- **Field research**: Audio notes and interviews
- **Accessibility**: Real-time speech-to-text

### 2. Edge AI Applications
- **Privacy**: No internet required
- **Latency**: Local processing
- **Reliability**: Works without cloud connectivity

### 3. IoT Integration
- **Smart speakers**: Local voice processing
- **Security systems**: Audio monitoring
- **Industrial**: Equipment audio analysis

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