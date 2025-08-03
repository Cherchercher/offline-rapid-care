# Jetson Setup Guide for Gemma 3n Medical Triage (Docker)

## Overview

This guide covers setting up the fine-tuned Gemma 3n model on NVIDIA Jetson using Docker for consistent, reproducible deployment.

## Quick Start (Docker)

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd offline-gemma
   ```

2. **Build and run with Docker**:
   ```bash
   ./build_and_run.sh
   ```

3. **Access the application**:
   - Web Interface: http://localhost:5050
   - Model API: http://localhost:5001
   - Upload Server: http://localhost:11435

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

### 2. Install Docker
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose
```

### 3. Verify Docker Installation
```bash
# Check Docker version
docker --version

# Test Docker with NVIDIA runtime
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.0-base nvidia-smi
```

## Docker Deployment

### 1. Build the Docker Image
```bash
# Build the Jetson-optimized image
./build_and_run.sh
```

This script will:
- Build the Docker image with Python 3.9 and all dependencies
- Download the 4B model inside the container
- Start all services (Flask app, Model server, Upload server)
- Mount necessary volumes for persistence

### 2. Manual Build (Alternative)
```bash
# Build only the Docker image
docker build -t offline-gemma-jetson .

# Run the container
docker run -d \
    --name offline-gemma-jetson \
    --runtime=nvidia \
    --gpus all \
    -p 5050:5050 \
    -p 5001:5001 \
    -p 11435:11435 \
    -v $(pwd)/models:/workspace/models \
    -v $(pwd)/uploads:/workspace/uploads \
    -v $(pwd)/rapidcare_offline.db:/workspace/rapidcare_offline.db \
    -v $(pwd)/offload:/workspace/offload \
    -v /etc/nv_tegra_release:/etc/nv_tegra_release:ro \
    -v /proc/device-tree/model:/proc/device-tree/model:ro \
    -v /tmp:/tmp \
    offline-gemma-jetson
```

### 3. Start Services
```bash
# Start all services inside the container
docker exec -d offline-gemma-jetson python3 serve_uploads.py
docker exec -d offline-gemma-jetson python3 model_server.py
```

## Model Management

### 1. Download Models (Inside Docker)
```bash
# Download 4B model inside container
docker exec offline-gemma-jetson python3 scripts/download_gemma_models.py --model 4b

# Check model status
docker exec offline-gemma-jetson ls -la /workspace/models/
```

### 2. Model Options

- **4B Model** (`cherchercher020/gemma-3N-finetune-100-injury-images`): ~8GB
  - Better performance and quality
  - Recommended for Jetson Nano with 4GB RAM
  - Includes injury detection capabilities

- **2B Model** (`google/gemma-3n-E2B-it`): ~4GB
  - Smaller and faster
  - Good for quick tasks
  - Basic multimodal capabilities

## Docker Architecture

### Services Running in Container
1. **Flask App** (port 5050): Main web interface
2. **Model API Server** (port 5001): AI model inference
3. **Upload Server** (port 11435): File upload handling

### Volume Mounts
- `./models` → `/workspace/models`: Model files
- `./uploads` → `/workspace/uploads`: Uploaded files
- `./rapidcare_offline.db` → `/workspace/rapidcare_offline.db`: Database
- `./offload` → `/workspace/offload`: Model offloading
- `/tmp` → `/tmp`: Temporary files
- Jetson-specific files for device detection

## Performance Expectations

### Docker Performance
- **Container startup**: 30-60 seconds
- **Model loading**: 30-90 seconds (4B), 20-60 seconds (2B)
- **Video processing**: 2-10 minutes (depending on file size)
- **Memory usage**: ~3.5GB (4B model)

### Optimization Tips
```bash
# Monitor container resources
docker stats offline-gemma-jetson

# View container logs
docker logs -f offline-gemma-jetson

# Check specific service logs
docker logs offline-gemma-jetson | grep "5001\|model_server"
```

## Usage Examples

### 1. Web Interface
```bash
# Access the main application
open http://localhost:5050

# Upload images/videos for medical triage
# Use the web interface for injury assessment
```

### 2. API Usage
```bash
# Test model API
curl -X POST http://localhost:5001/chat/text \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":[{"type":"text","text":"Hello"}]}]}'

# Test video processing
curl -X POST http://localhost:5001/test-video-simple \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":[{"type":"video","path":"/tmp/test.mp4"}]}]}'
```

### 3. Log Monitoring
```bash
# View all logs with color coding
./scripts/view_all_logs.sh

# View specific service logs
./scripts/view_model_logs.sh    # Model server
./scripts/view_flask_logs.sh    # Flask app
./scripts/view_upload_logs.sh   # Upload server
```

## Troubleshooting

### Common Docker Issues

1. **Permission Denied**
   ```bash
   # Fix Docker permissions
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **Out of Memory**
   ```bash
   # Check container memory usage
   docker stats offline-gemma-jetson
   
   # Restart container
   docker restart offline-gemma-jetson
   ```

3. **Model Not Loading**
   ```bash
   # Check if model files exist
   docker exec offline-gemma-jetson ls -la /workspace/models/
   
   # Download models again
   docker exec offline-gemma-jetson python3 scripts/download_gemma_models.py --model 4b
   ```

4. **Port Already in Use**
   ```bash
   # Stop existing container
   docker stop offline-gemma-jetson
   docker rm offline-gemma-jetson
   
   # Rebuild and run
   ./build_and_run.sh
   ```

### Debug Commands
```bash
# Check container status
docker ps

# View all logs
docker logs offline-gemma-jetson

# Enter container shell
docker exec -it offline-gemma-jetson bash

# Check GPU access
docker exec offline-gemma-jetson nvidia-smi

# Test model server
curl http://localhost:5001/health
```

## Docker Commands Reference

### Container Management
```bash
# Start container
docker start offline-gemma-jetson

# Stop container
docker stop offline-gemma-jetson

# Remove container
docker rm offline-gemma-jetson

# Rebuild image
docker build -t offline-gemma-jetson .
```

### Log Management
```bash
# View real-time logs
docker logs -f offline-gemma-jetson

# View last 100 lines
docker logs --tail 100 offline-gemma-jetson

# View logs since timestamp
docker logs --since "2024-01-01T00:00:00" offline-gemma-jetson
```

### Volume Management
```bash
# List volumes
docker volume ls

# Backup data
docker cp offline-gemma-jetson:/workspace/rapidcare_offline.db ./backup/

# Restore data
docker cp ./backup/rapidcare_offline.db offline-gemma-jetson:/workspace/
```

## Comparison with Native Installation

| Aspect | Docker | Native |
|--------|--------|--------|
| **Setup Time** | 5 minutes | 30+ minutes |
| **Dependencies** | Automatic | Manual |
| **Reproducibility** | High | Low |
| **Isolation** | Complete | System-wide |
| **Updates** | Rebuild image | Update system |
| **Debugging** | Container logs | System logs |

## Conclusion

Docker deployment on Jetson provides:
- ✅ **Consistent environment** across different Jetson devices
- ✅ **Easy setup** with single command
- ✅ **Isolated dependencies** (no system conflicts)
- ✅ **Reproducible builds** (same image everywhere)
- ✅ **Easy updates** (rebuild image)
- ✅ **Simple debugging** (container logs)

The Docker approach is recommended for production deployment and development.

### Extras
Screen recording in Jetson:
```bash
gst-launch-1.0 ximagesrc num-buffers=100 use-damage=0 ! video/x-raw ! nvvidconv ! 'video/x-raw(memory:NVMM),format=NV12' ! nvv4l2h264enc ! h264parse ! qtmux ! filesink location=a.mp4
```