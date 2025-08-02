# Docker Deployment for Jetson Xavier

This guide covers deploying the Offline Gemma application on Jetson Xavier using Docker.

## Prerequisites

### 1. Jetson Xavier Setup
- Jetson Xavier NX or AGX Xavier
- JetPack 4.6.3 or later
- At least 32GB storage (64GB recommended)
- 4GB+ RAM

### 2. Docker Installation
```bash
# Install Docker on Jetson
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install NVIDIA Docker runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 3. Verify Installation
```bash
# Test Docker
docker --version

# Test NVIDIA Docker
sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

## Quick Start

### Option 1: Using the Build Script (Recommended)
```bash
# Clone the repository
git clone <your-repo>
cd offline-gemma

# Run the build and deployment script (includes model download)
./build_and_run.sh
```

or 
```
# Rebuild container with all fixes
sudo docker stop offline-gemma-jetson
sudo docker rm offline-gemma-jetson
sudo docker build -t offline-gemma-jetson .
./build_and_run.sh
```

**Note**: The build script will automatically download the finetuned 4B model (~8GB) if it's not already present.

### Option 2: Manual Docker Commands
```bash
# Build the image
docker build -t offline-gemma-jetson .

# Run the container
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
```

### Option 3: Using Docker Compose
```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Directory Structure

The Docker setup uses the following directory structure:

```
offline-gemma/
├── models/           # Model files (mounted as volume)
├── uploads/          # Temporary uploads (mounted as volume)
├── offload/          # Model offloading (mounted as volume)
├── rapidcare_offline.db  # Database file (mounted as volume)
├── Dockerfile        # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── build_and_run.sh  # Build and run script
└── .dockerignore     # Docker ignore file
```

## Model Setup

### 1. Download Models (Automatic)
The build script automatically downloads the finetuned 4B model. However, you can also download models manually:

```bash
# Download models using the interactive script
./download_models.sh

# Or download directly using Python
python3 scripts/download_gemma_models.py --model 4b --check-space

# Or download both models if you have enough space
python3 scripts/download_gemma_models.py --model both --check-space
```

**Available Models:**
- **4B Finetuned** (`cherchercher020/gemma-3N-finetune-100-injury-images`): ~8GB
  - **Recommended for Jetson Xavier**
  - Includes injury detection capabilities
  - Better performance and quality
- **2B Base** (`google/gemma-3n-E2B-it`): ~4GB
  - Smaller and faster
  - Basic multimodal capabilities

### 2. Model Placement
Place the downloaded models in the `models/` directory:
```
models/
├── gemma3n-4b/
│   ├── config.json
│   ├── model.safetensors
│   └── ...
└── gemma3n-2b/
    ├── config.json
    ├── model.safetensors
    └── ...
```

## Usage

### 1. Access the Application
- **Web Interface**: http://localhost:5050
- **API Endpoints**: http://localhost:5050/api/*

### 2. Monitor the Application
```bash
# View container logs
docker logs -f offline-gemma-jetson

# Check container status
docker ps

# Monitor system resources
docker stats offline-gemma-jetson
```

### 3. Stop the Application
```bash
# Stop the container
docker stop offline-gemma-jetson

# Remove the container
docker rm offline-gemma-jetson

# Or using docker-compose
docker-compose down
```

## Configuration

### Environment Variables
You can customize the application by setting environment variables:

```bash
docker run -d \
    --name offline-gemma-jetson \
    --runtime=nvidia \
    --gpus all \
    -p 5050:5050 \
    -e FLASK_ENV=production \
    -e PYTHONUNBUFFERED=1 \
    -v $(pwd)/models:/workspace/models \
    -v $(pwd)/uploads:/workspace/uploads \
    -v $(pwd)/rapidcare_offline.db:/workspace/rapidcare_offline.db \
    -v $(pwd)/offload:/workspace/offload \
    --restart unless-stopped \
    offline-gemma-jetson
```

### Port Configuration
To change the port, modify the port mapping:
```bash
# Change from 5050 to 8080
-p 8080:5050
```

## Troubleshooting

### 1. GPU Not Detected
```bash
# Check if NVIDIA Docker is working
sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# If not working, reinstall nvidia-docker2
sudo apt-get remove nvidia-docker2
sudo apt-get install nvidia-docker2
sudo systemctl restart docker
```

### 2. Container Won't Start
```bash
# Check container logs
docker logs offline-gemma-jetson

# Check if ports are available
sudo netstat -tulpn | grep 5050

# Kill any process using the port
sudo kill -9 $(sudo lsof -t -i:5050)
```

### 3. Out of Memory
```bash
# Check available memory
free -h

# Increase swap space if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 4. Model Loading Issues
```bash
# Check if models are properly mounted
docker exec -it offline-gemma-jetson ls -la /workspace/models

# Check model file permissions
docker exec -it offline-gemma-jetson ls -la /workspace/models/gemma3n-4b/
```

### 5. Performance Issues
```bash
# Monitor GPU usage
nvidia-smi

# Monitor container resources
docker stats offline-gemma-jetson

# Check system load
htop
```

## Maintenance

### 1. Update the Application
```bash
# Pull latest changes
git pull

# Rebuild the image
docker build -t offline-gemma-jetson .

# Restart the container
docker stop offline-gemma-jetson
docker rm offline-gemma-jetson
./build_and_run.sh
```

### 2. Clean Up
```bash
# Remove unused images
docker image prune -a

# Remove unused containers
docker container prune

# Remove unused volumes
docker volume prune
```

### 3. Backup
```bash
# Backup the database
cp rapidcare_offline.db rapidcare_offline.db.backup

# Backup models (if needed)
tar -czf models_backup.tar.gz models/
```

## Security Considerations

1. **Network Security**: The application runs on localhost by default. For production, consider using a reverse proxy.

2. **File Permissions**: Ensure proper file permissions for mounted volumes.

3. **Resource Limits**: Consider setting memory and CPU limits for the container.

4. **Updates**: Regularly update the base images and dependencies.

## Support

For issues specific to Jetson Xavier deployment:
1. Check the container logs: `docker logs offline-gemma-jetson`
2. Verify GPU availability: `nvidia-smi`
3. Check system resources: `htop`
4. Review the main README.md for application-specific issues 