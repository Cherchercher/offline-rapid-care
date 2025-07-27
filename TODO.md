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

### **3.3 Download Gemma 3n Model**
```bash
# Create models directory
mkdir -p models/gemma3n-local

# Download the Gemma 3n model
# Option 1: Download from Hugging Face (requires internet)
python3 scripts/download_gemma_local.py

# Option 2: Copy model files from another device
# scp -r user@source-device:/path/to/gemma3n-local models/
```

---

## **Phase 4: Model Optimization for Jetson**

### **4.1 Optimize Model for Jetson**
```bash
# Run model optimization scripts
python3 scripts/check_model_dtype.py
python3 scripts/reduce_model_size.py

# For aggressive optimization (if needed)
python3 scripts/aggressive_reduction.py
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
   ls -la models/gemma3n-local/
   
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