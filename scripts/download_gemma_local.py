#!/usr/bin/env python3
"""
Download Gemma 3n model locally for direct inference
"""

import os
import torch
from transformers import AutoProcessor, Gemma3nForConditionalGeneration
from huggingface_hub import snapshot_download

def download_gemma_local():
    """Download Gemma 3n model locally"""
    
    model_id = "google/gemma-3n-E2B-it"
    local_dir = "./models/gemma3n-local-e2b"
    
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

def create_model_config(local_path):
    """Create a model configuration file"""
    
    config_content = f"""# Model Configuration
model_path: {local_path}
model_type: gemma3n
temperature: 0.1
top_p: 0.9
top_k: 40
max_length: 32768
repeat_penalty: 1.1

# System prompt for medical triage
system_prompt: "You are a medical triage assistant trained for mass casualty incidents. You can process and transcribe audio files accurately. You can analyze images and videos for medical assessment. You can handle text, audio, image, and video inputs. When given audio files, transcribe them completely and accurately. When analyzing medical images or videos, provide triage assessments."
"""
    
    with open("model_config.yaml", "w") as f:
        f.write(config_content)
    
    print("📝 Created model_config.yaml")
    return "model_config.yaml"

if __name__ == "__main__":
    print("🚀 Setting up local Gemma 3n model...")
    
    # Download model
    local_path = download_gemma_local()
    
    if local_path:
        # Create model configuration
        config = create_model_config(local_path)
        
        print("\n📋 Next steps:")
        print("1. Model downloaded successfully!")
        print(f"2. Configuration saved to: {config}")
        print("3. Use the model directly in Python for full capabilities")
        
        print("\n🎯 For direct Python usage:")
        print("   from transformers import AutoProcessor, AutoModelForImageTextToText")
        print(f"   model = AutoModelForImageTextToText.from_pretrained('{local_path}')")
        print(f"   processor = AutoProcessor.from_pretrained('{local_path}')")
        print("\n💡 This model supports audio, image, and video processing")
    else:
        print("❌ Failed to download model") 