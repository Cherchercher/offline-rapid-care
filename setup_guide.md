# RapidCare Setup Guide

## 🚀 Quick Setup

### Option 1: Ollama Mode (Recommended for Production)
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull the base Gemma 3n model
ollama pull gemma3n:e4b

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

#### For Ollama (Custom Model):
```bash
# 1. Create a Modelfile for your fine-tuned model
cat > Modelfile << EOF
FROM gemma3n:e4b
PARAMETER temperature 0.7
PARAMETER top_p 0.9
SYSTEM """You are a medical triage assistant trained for mass casualty incidents.
Respond with concise, actionable information using medical triage categories."""
EOF

# 2. Build custom model
ollama create mci-triage -f Modelfile

# 3. Update app.py to use your custom model
# Change GEMMA_MODEL = "mci-triage"
```

### 2. Environment Configuration

Create `.env` file:
```bash
# Model Configuration
MODEL_MODE=auto                    # auto, direct, or ollama
OLLAMA_URL=http://localhost:11434
GEMMA_MODEL=gemma3n:e4b           # or your custom model name

# Video Processing
VIDEO_FRAME_INTERVAL=2
VIDEO_MAX_FRAMES=10
VIDEO_IMAGE_SIZE=512

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Security
SECRET_KEY=your-secret-key-here
```

### 3. Ollama Setup (if using Ollama mode)

#### Install Ollama:
```bash
# macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

#### Verify Installation:
```bash
# Check Ollama version
ollama --version

# List available models
ollama list

# Test model
ollama run gemma3n:e4b "Hello, test message"
```

#### Pull Required Models:
```bash
# Pull base model
ollama pull gemma3n:e4b

# If you have a custom fine-tuned model:
# ollama pull your-custom-model-name
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

### 2. Test Ollama Connection:
```bash
curl http://localhost:11434/api/tags
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

#### 2. Ollama Connection Issues:
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama
sudo systemctl restart ollama

# Check logs
journalctl -u ollama -f
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
export MODEL_MODE=ollama
export OLLAMA_URL=http://your-ollama-server:11434
export FLASK_ENV=production
```

## 📞 Support

If you encounter issues:
1. Check the logs in the console
2. Verify all dependencies are installed
3. Ensure sufficient memory/GPU resources
4. Test with a simple example first

For additional help, refer to the main README_PWA.md file. 