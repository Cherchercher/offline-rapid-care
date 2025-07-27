# RapidCare Setup Guide

## 🚀 Quick Setup

### Option 1: Direct Model Mode (Recommended for Production)
```bash
# 1. Download the Gemma 3n model
python3 scripts/download_gemma_models.py --model 2b

# 2. Test the model
python3 scripts/dynamic_model_manager.py

# 3. Run the startup script
./start.sh
```

### Option 2: Direct Model Loading (Development/Offline)
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Run with direct model loading
python app.py --mode direct
```

## 📁 Model File Structure

```
offline-gemma/
├── models/                          # Model storage directory
│   ├── base/                        # Base models
│   │   └── gemma3n-e4b/            # Base Gemma 3n model
│   ├── fine-tuned/                  # Fine-tuned models
│   │   ├── mci-triage-lora/        # Your fine-tuned LoRA adapter
│   │   └── mci-role-specific/      # Role-specific fine-tuned models
│   └── configs/                     # Model configurations
│       ├── triage_config.json
│       └── role_configs.json
├── app.py                          # Main Flask application
├── model_manager.py                # Model management
├── video_processor.py              # Video processing
└── start.sh                        # Startup script
```

## 🔧 Detailed Setup Instructions

### 1. Fine-tuned Model Setup

#### For Direct Model Loading:
```bash
# Create model directories
mkdir -p models/fine-tuned/mci-triage-lora
mkdir -p models/configs

# Place your fine-tuned model files:
# - adapter_config.json
# - adapter_model.bin (or pytorch_model.bin)
# - tokenizer files
# - config.json

# Example structure:
models/fine-tuned/mci-triage-lora/
├── adapter_config.json
├── adapter_model.bin
├── tokenizer.json
├── tokenizer_config.json
└── special_tokens_map.json
```

#### For Direct Model (Custom Model):
```bash
# 1. Create a model configuration file
cat > models/configs/triage_config.json << EOF
{
  "model_name": "gemma3n-2b",
  "temperature": 0.7,
  "top_p": 0.9,
  "system_prompt": "You are a medical triage assistant trained for mass casualty incidents. Respond with concise, actionable information using medical triage categories."
}
EOF

# 2. Update app.py to use your custom configuration
# Change MODEL_CONFIG = "models/configs/triage_config.json"
```

### 2. Environment Configuration

Create `.env` file:
```bash
# Model Configuration
MODEL_MODE=auto                    # auto, direct, or edge_ai
GEMMA_MODEL=gemma3n-2b           # or your custom model name

# Video Processing
VIDEO_FRAME_INTERVAL=2
VIDEO_MAX_FRAMES=10
VIDEO_IMAGE_SIZE=512

# Flask Configuration
FLASK_ENV=development
```

## 🔧 Important System Configuration Files

### **Nginx Configuration**
**File**: `/etc/nginx/conf.d/emr.nomadichacker.com.conf`
**Purpose**: Web server configuration for production deployment
**Key Settings**:
```nginx
client_max_body_size 500M;  # File upload limit
proxy_connect_timeout 600s;  # Connection timeout
proxy_send_timeout 600s;     # Send timeout
proxy_read_timeout 600s;     # Read timeout
send_timeout 600s;           # Response timeout
```

### **Application Configuration Files**
| File | Purpose | Key Settings |
|------|---------|--------------|
| `app.py` | Main Flask application | Port 5050, CORS settings |
| `model_server.py` | AI model API server | Port 5001, model loading |
| `serve_uploads.py` | File upload server | Port 11435, file serving |
| `tmux_start.sh` | Service startup script | Process management |
| `tmux_stop.sh` | Service shutdown script | Process cleanup |

### **Model Configuration**
| File | Purpose | Location |
|------|---------|----------|
| `./models/gemma3n-2b/` | 2B model directory | Local storage |
| `./models/gemma3n-4b/` | 4B model directory | Local storage |
| `model_manager_pipeline.py` | Model loading logic | Dynamic selection |

### **Database Files**
| File | Purpose | Description |
|------|---------|-------------|
| `rapidcare_offline.db` | SQLite database | Patient data, offline tasks |
| `database_setup.py` | Database initialization | Schema creation |

### **Environment Configuration**
| File | Purpose | Key Variables |
|------|---------|---------------|
| `requirements.txt` | Python dependencies | Flask, transformers, torch |
| `.gitignore` | Version control exclusions | Models, databases, logs |

### **Service Management**
| File | Purpose | Commands |
|------|---------|---------|
| `start.sh` | Application startup | `./start.sh` |
| `tmux_start.sh` | Service startup | `./tmux_start.sh` |
| `tmux_stop.sh` | Service shutdown | `./tmux_stop.sh` |

### **Testing and Validation**
| File | Purpose | Usage |
|------|---------|-------|
| `scripts/test_load.py` | Load testing | `python scripts/test_load.py` |
| `scripts/jetson_load_monitor.py` | System monitoring | `python scripts/jetson_load_monitor.py` |

### **Production Deployment Checklist**
1. **Nginx Configuration**: Update `/etc/nginx/conf.d/emr.nomadichacker.com.conf`
2. **File Size Limits**: Set `client_max_body_size 500M`
3. **Timeout Settings**: Configure proxy timeouts for long-running AI tasks
4. **Model Directories**: Ensure models are in `./models/gemma3n-2b/` and `./models/gemma3n-4b/`
5. **Service Startup**: Use `tmux_start.sh` for production deployment
6. **Database**: Initialize with `python database_setup.py`
7. **Permissions**: Ensure proper file permissions for uploads and models
FLASK_DEBUG=1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Security
SECRET_KEY=your-secret-key-here
```

### 3. Direct Model Setup (if using Direct mode)

#### Download Models:
```bash
# Download 2B model (for CPU environments)
python3 scripts/download_gemma_models.py --model 2b

# Download 4B model (for GPU environments)
python3 scripts/download_gemma_models.py --model 4b

# Download both models
python3 scripts/download_gemma_models.py --model both
```

#### Verify Installation:
```bash
# Test model loading
python3 scripts/dynamic_model_manager.py

# Test model availability
python3 scripts/setup_model_directories.py
```

#### Model Configuration:
```bash
# Setup model directories
python3 scripts/setup_model_directories.py

# Test model selection
python3 scripts/dynamic_model_manager.py
```

### 4. Python Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually:
pip install torch>=2.4.0
pip install transformers>=4.53.0
pip install Flask>=2.3.0
pip install opencv-python>=4.8.0
pip install Pillow>=10.0.0
pip install numpy>=1.24.0
pip install requests>=2.31.0
```

### 5. GPU Setup (Optional but Recommended)

#### CUDA Setup:
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA version of PyTorch if needed
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Memory Requirements:
- **Minimum**: 8GB RAM
- **Recommended**: 16GB+ RAM
- **GPU**: 8GB+ VRAM for optimal performance

## 🎯 Model Integration

### Using Your Fine-tuned Model

#### 1. Update Model Manager Configuration:
```python
# In model_manager.py
class ModelManager:
    def __init__(self, mode="auto", model_path="models/fine-tuned/mci-triage-lora"):
        self.model_path = model_path
        # ... rest of initialization
```

#### 2. Load Fine-tuned Model:
```python
def _load_direct_model(self):
    # Load base model
    base_model = AutoModelForImageTextToText.from_pretrained("google/gemma-3n-E4B-it")
    
    # Load your LoRA adapter
    from peft import PeftModel
    self.direct_model = PeftModel.from_pretrained(base_model, self.model_path)
```

#### 3. Update App Configuration:
```python
# In app.py
GEMMA_MODEL = "mci-triage"  # Your custom model name
MODEL_PATH = "models/fine-tuned/mci-triage-lora"
```

## 🧪 Testing Your Setup

### 1. Test Model Loading:
```bash
python -c "
from model_manager import ModelManager
mm = ModelManager(mode='direct')
print('Model loaded successfully')
"
```

### 2. Test Model Connection:
```bash
curl http://localhost:5001/chat
```

### 3. Test Video Processing:
```bash
python video_processor.py
```

### 4. Test Full Application:
```bash
./start.sh
# Then visit http://localhost:5000
```

## 🔍 Troubleshooting

### Common Issues:

#### 1. Model Loading Errors:
```bash
# Check available memory
free -h

# Check GPU memory
nvidia-smi

# Try loading with CPU only
export CUDA_VISIBLE_DEVICES=""
```

#### 2. Model Connection Issues:
```bash
# Check if model server is running
ps aux | grep model_server

# Restart model server
pkill -f model_server
python3 model_server.py &

# Check logs
tail -f model_server.log
```

#### 3. Video Processing Issues:
```bash
# Install OpenCV dependencies
sudo apt-get install libopencv-dev python3-opencv

# Check video codecs
ffmpeg -codecs | grep h264
```

#### 4. Memory Issues:
```bash
# Reduce model precision
export TORCH_DTYPE=float16

# Use gradient checkpointing
export GRADIENT_CHECKPOINTING=1
```

## 📊 Performance Optimization

### 1. Model Optimization:
```python
# Use quantization for faster inference
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)
```

### 2. Video Processing Optimization:
```python
# Reduce frame processing
VIDEO_FRAME_INTERVAL = 5  # Process every 5th frame
VIDEO_MAX_FRAMES = 5      # Limit to 5 frames
```

### 3. Caching:
```python
# Enable model caching
export TRANSFORMERS_CACHE="/path/to/cache"
export HF_HOME="/path/to/huggingface"
```

## 🚀 Production Deployment

### 1. Using Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. Using Docker:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### 3. Environment Variables:
```bash
export MODEL_MODE=direct
export FLASK_ENV=production
```

## 📞 Support

If you encounter issues:
1. Check the logs in the console
2. Verify all dependencies are installed
3. Ensure sufficient memory/GPU resources
4. Test with a simple example first

For additional help, refer to the main README_PWA.md file. 