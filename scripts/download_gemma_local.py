#!/usr/bin/env python3
"""
Download Gemma 3n model locally for use with Ollama or direct inference
"""

import os
import torch
from transformers import AutoProcessor, Gemma3nForConditionalGeneration
from huggingface_hub import snapshot_download

def download_gemma_local():
    """Download Gemma 3n model locally"""
    
    model_id = "google/gemma-3n-E2B-it"
    local_dir = "./models/gemma3n-local"
    
    print(f"📥 Downloading {model_id} to {local_dir}...")
    
    # Create directory
    os.makedirs(local_dir, exist_ok=True)
    
    try:
        # Download model files
        snapshot_download(
            repo_id=model_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        
        print("✅ Model downloaded successfully!")
        print(f"📁 Model location: {os.path.abspath(local_dir)}")
        
        # Test loading
        print("🧪 Testing model loading...")
        processor = AutoProcessor.from_pretrained(local_dir)
        model = Gemma3nForConditionalGeneration.from_pretrained(
            local_dir,
            torch_dtype=torch.float32,  # Use float32 for CPU
            device_map="cpu",           # Force CPU usage
            low_cpu_mem_usage=True      # Use low CPU memory
        )
        
        print("✅ Model loaded successfully!")
        print("🎯 This model has full audio, image, and video capabilities")
        
        return local_dir
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return None

def create_ollama_modelfile(local_path):
    """Create a Modelfile for Ollama using local model"""
    
    modelfile_content = f"""FROM {local_path}

# This model has full audio, image, and video capabilities
SYSTEM "You are an AI assistant with comprehensive multimodal capabilities. You can process and transcribe audio files accurately. You can analyze images and videos. You can handle text, audio, image, and video inputs. When given audio files, transcribe them completely and accurately."

# Set parameters optimized for audio processing
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 32768
PARAMETER repeat_penalty 1.1
"""
    
    with open("Modelfile.local", "w") as f:
        f.write(modelfile_content)
    
    print("📝 Created Modelfile.local for Ollama")
    return "Modelfile.local"

if __name__ == "__main__":
    print("🚀 Setting up local Gemma 3n model...")
    
    # Download model
    local_path = download_gemma_local()
    
    if local_path:
        # Create Ollama Modelfile
        modelfile = create_ollama_modelfile(local_path)
        
        print("\n📋 Next steps:")
        print("1. Build Ollama model:")
        print(f"   ollama create gemma3n-local -f {modelfile}")
        print("2. Update your app to use 'gemma3n-local'")
        print("3. Or use the model directly in Python for full audio support")
        
        print("\n🎯 For direct Python usage (recommended for audio):")
        print("   from transformers import AutoProcessor, Gemma3nForConditionalGeneration")
        print(f"   model = Gemma3nForConditionalGeneration.from_pretrained('{local_path}')")
        print("   processor = AutoProcessor.from_pretrained('{local_path}')")
    else:
        print("❌ Failed to download model") 