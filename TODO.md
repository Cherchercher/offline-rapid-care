# RapidCare Jetson Setup TODO

## 🚀 Jetson Device Setup for RapidCare

### **Prerequisites**
- [ ] NVIDIA Jetson device (Nano, Xavier NX, AGX Xavier, or newer)
- [ ] Jetson device flashed with JetPack 5.0+ (recommended: JetPack 5.1.1)
- [ ] At least 8GB of free storage space
- [ ] Internet connection for initial setup

---

## **Phase 1: System Preparation**

### **1.1 Update Jetson System**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential cmake git wget curl

# Install Python development tools
sudo apt install -y python3-dev python3-pip python3-venv
```

### **1.2 Install CUDA and cuDNN Dependencies**
```bash
# Verify CUDA installation
nvcc --version
nvidia-smi

# Install cuDNN (if not already included in JetPack)
# Note: cuDNN is typically pre-installed in JetPack
```

### **1.3 Install System Dependencies**
```bash
# Install audio/video processing dependencies
sudo apt install -y ffmpeg libavcodec-dev libavformat-dev libswscale-dev

# Install image processing libraries
sudo apt install -y libopencv-dev python3-opencv

# Install additional system libraries
sudo apt install -y libssl-dev libffi-dev libjpeg-dev libpng-dev
```

---

## **Phase 2: Python Environment Setup**

### **2.1 Create Virtual Environment**
```bash
# Create project directory
mkdir -p ~/rapidcare
cd ~/rapidcare

# Create virtual environment
python3 -m venv rapidcare_env
source rapidcare_env/bin/activate
```

### **2.2 Install PyTorch for Jetson**
```bash
# Install PyTorch with CUDA support for Jetson
# Use the official Jetson PyTorch wheel
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify PyTorch CUDA support
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device count: {torch.cuda.device_count()}')"
```

### **2.3 Install Transformers and Dependencies**
```bash
# Install transformers with CUDA support
pip3 install transformers[torch] accelerate

# Install additional ML libraries
pip3 install sentencepiece protobuf

# Install audio processing libraries
pip3 install librosa soundfile pydub

# Install image processing libraries
pip3 install Pillow opencv-python
```

---

## **Phase 3: RapidCare Installation**

### **3.1 Clone Repository**
```bash
# Clone the RapidCare repository
git clone <repository-url> .
# OR if you have the files locally, copy them to ~/rapidcare/
```

### **3.2 Install Python Dependencies**
```bash
# Install requirements
pip3 install -r requirements.txt

# Install additional Jetson-specific packages
pip3 install psutil  # For memory monitoring
pip3 install requests  # For HTTP requests
```

### **3.3 Download Gemma 3n Models**
```bash
# Create models directory
mkdir -p models/

# Download both 2B and 4B models (recommended for Jetson Xavier NX)
python3 scripts/download_gemma_models.py --model both --check-space

# Or download individual models:
# python3 scripts/download_gemma_models.py --model 2b  # For CPU environments
# python3 scripts/download_gemma_models.py --model 4b  # For GPU environments

# Option 2: Copy model files from another device
# scp -r user@source-device:/path/to/gemma3n-2b models/
# scp -r user@source-device:/path/to/gemma3n-4b models/
```

---

## **Phase 4: Model Optimization for Jetson**

### **4.1 Configure Model Paths**
```bash
# Set up model directory structure
mkdir -p models/gemma3n-2b models/gemma3n-4b

# Option 1: Use Dynamic Model Manager (Recommended)
# The dynamic model manager automatically selects the best model based on:
# - System load (CPU, memory, GPU usage)
# - Device capabilities (Jetson vs Desktop)
# - Task type (quick vs complex analysis)

# Setup model directories (renames existing gemma3n-local to gemma3n-2b)
python3 scripts/setup_model_directories.py

# Test dynamic model selection
python3 scripts/dynamic_model_manager.py

# Option 2: Manual Configuration
# Edit model_manager_pipeline.py to use specific model:
# - Default: ./models/gemma3n-2b (for web/CPU environments)
# - Jetson: ./models/gemma3n-4b (for GPU environments)

# Test model loading
python3 scripts/test_setup.py
```

### **4.2 Optimize Models for Jetson**
```bash
# Run model optimization scripts
python3 scripts/check_model_dtype.py
python3 scripts/reduce_model_size.py

# For aggressive optimization (if needed)
python3 scripts/aggressive_reduction.py
```

### **4.3 Integrate Dynamic Model Manager**
```bash
# Update your main application to use dynamic model selection
# In model_manager_pipeline.py, replace the static model path with:

from scripts.dynamic_model_manager import DynamicModelManager

class ModelManagerPipeline:
    def __init__(self):
        self.dynamic_manager = DynamicModelManager()
        self.model = None
        self.processor = None
    
    def load_model(self, task_type='general'):
        """Load the optimal model for the current task and system load"""
        self.model, self.processor = self.dynamic_manager.load_model()
        return self.model, self.processor
    
    def select_model_for_task(self, task_type):
        """Select the best model for a specific task"""
        return self.dynamic_manager.select_optimal_model(task_type)
```

### **4.4 Model Directory Configuration Options**

#### **Option A: Dynamic Selection (Recommended)**
```bash
# Models are automatically selected based on system load
./models/gemma3n-2b/  # Used for high load, quick tasks
./models/gemma3n-4b/  # Used for low load, complex tasks
```

#### **Option B: Static Configuration**
```bash
# For Web/CPU environments (default)
./models/gemma3n-local-e2b/  # Rename to gemma3n-2b for consistency

# For Jetson/GPU environments
./models/gemma3n-local-e4b/     # Use 4B model for better performance
```

#### **Option C: Environment-Specific**
```bash
# Set environment variable to override default
export RAPIDCARE_MODEL_PATH="./models/gemma3n-4b"

# Or use command line argument
python3 app.py --model-path ./models/gemma3n-4b
```

### **4.2 Test Model Loading**
```bash
# Test model loading on Jetson
python3 scripts/test_setup.py

# Test model inference
python3 model_server.py
```

---

## **Phase 5: System Configuration**

### **5.1 Configure System Services**
```bash
# Create systemd service for auto-start (optional)
sudo nano /etc/systemd/system/rapidcare.service

# Add the following content:
[Unit]
Description=RapidCare MCI Response System
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/rapidcare
Environment=PATH=/home/jetson/rapidcare/rapidcare_env/bin
ExecStart=/home/jetson/rapidcare/rapidcare_env/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable rapidcare
sudo systemctl start rapidcare
```

### **5.2 Configure Firewall (if needed)**
```bash
# Allow RapidCare ports
sudo ufw allow 5050  # Flask app
sudo ufw allow 5001  # Model server
sudo ufw allow 11435 # Uploads server
```

---

## **Phase 6: Performance Optimization**

### **6.1 Jetson Performance Tuning**
```bash
# Set Jetson to maximum performance mode
sudo nvpmodel -m 0  # Maximum performance
sudo jetson_clocks  # Enable all clocks

# Verify performance mode
sudo nvpmodel -q
```

### **6.2 Memory and Storage Optimization**
```bash
# Check available memory
free -h

# Check storage space
df -h

# Optimize swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## **Phase 7: Testing and Validation**

### **7.1 Test Offline Storage**
```bash
# Test offline storage functionality
python3 scripts/test_offline_storage.py

# Test device capabilities detection
python3 -c "from offline_storage_manager import offline_storage; print(offline_storage.get_device_capabilities())"
```

### **7.2 Test Model Server**
```bash
# Start model server
python3 model_server.py

# Test in another terminal
curl http://localhost:5001/health
```

### **7.3 Test Full Application**
```bash
# Start the full application
./start.sh

# Or start with TMUX
./tmux_start.sh

# Test web interface
# Open browser to http://jetson-ip:5050
```

---

## **Phase 8: Production Deployment**

### **8.1 Environment Variables**
```bash
# Create environment file
nano .env

# Add the following:
FLASK_ENV=production
FLASK_DEBUG=0
CUDA_VISIBLE_DEVICES=0
TORCH_CUDA_ARCH_LIST="7.2;8.7"  # For Jetson Xavier
```

### **8.2 Logging Configuration**
```bash
# Create logs directory
mkdir -p logs

# Configure log rotation
sudo nano /etc/logrotate.d/rapidcare

# Add content:
/home/jetson/rapidcare/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 jetson jetson
}
```

---

## **Phase 9: Monitoring and Maintenance**

### **9.1 System Monitoring**
```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor system resources
htop

# Monitor application logs
tail -f logs/rapidcare.log
```

### **9.2 Regular Maintenance**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean up old logs
find logs/ -name "*.log" -mtime +7 -delete

# Check disk space
df -h

# Monitor offline storage
python3 -c "from offline_storage_manager import offline_storage; print(offline_storage.get_storage_stats())"
```

---

## **Troubleshooting**

### **Common Issues:**

1. **CUDA Out of Memory**
   ```bash
   # Reduce model precision
   python3 scripts/aggressive_reduction.py
   
   # Or increase swap
   sudo fallocate -l 8G /swapfile
   ```

2. **Model Loading Fails**
   ```bash
   # Check model files
   ls -la models/gemma3n-local-e4b/
   ls -la models/gemma3n-local-e2b/
   # Re-download model
   python3 scripts/download_gemma_local.py
   ```

3. **Port Already in Use**
   ```bash
   # Find process using port
   sudo netstat -tulpn | grep :5050
   
   # Kill process
   sudo kill -9 <PID>
   ```

4. **Permission Issues**
   ```bash
   # Fix ownership
   sudo chown -R jetson:jetson ~/rapidcare
   
   # Fix permissions
   chmod +x *.sh
   ```

---

## **Performance Benchmarks**

### **Expected Performance on Jetson:**
- **Jetson Nano**: Limited offline processing, recommend online mode
- **Jetson Xavier NX**: Good offline processing capability
- **Jetson AGX Xavier**: Excellent offline processing capability

### **Memory Requirements:**
- **Model Loading**: ~4GB RAM
- **Inference**: ~2GB RAM per concurrent request
- **Offline Storage**: ~1GB for temporary files

---

## **Security Considerations**

### **Network Security:**
- [ ] Configure firewall rules
- [ ] Use HTTPS in production
- [ ] Implement authentication if needed

### **Data Security:**
- [ ] Encrypt offline storage
- [ ] Secure model files
- [ ] Regular security updates

---

## **Backup and Recovery**

### **Backup Strategy:**
```bash
# Backup configuration
tar -czf rapidcare-config-$(date +%Y%m%d).tar.gz *.py *.sh requirements.txt

# Backup models
tar -czf rapidcare-models-$(date +%Y%m%d).tar.gz models/

# Backup offline storage
tar -czf rapidcare-offline-$(date +%Y%m%d).tar.gz offline_storage/
```

---

## **Next Steps After Setup:**

1. **Test all functionality** in both online and offline modes
2. **Configure cloud sync** endpoints for your specific use case
3. **Set up monitoring** and alerting
4. **Train team members** on system operation
5. **Document procedures** for your specific deployment
6. **Plan regular maintenance** schedule

---

## **Support and Resources:**

- **Jetson Documentation**: https://developer.nvidia.com/embedded/learn/get-started-jetson-nano-devkit
- **PyTorch Jetson**: https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/70
- **RapidCare Issues**: Create GitHub issue for bugs or feature requests

---

**Last Updated**: $(date)
**Version**: 1.0
**Jetson Compatibility**: Nano, Xavier NX, AGX Xavier, Orin 