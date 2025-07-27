#!/usr/bin/env python3
"""
Download Gemma 3n models (2B and 4B) for Jetson deployment
"""

import os
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from huggingface_hub import snapshot_download
import argparse

def download_gemma_model(model_size: str = "2b", local_dir: str = None):
    """Download Gemma 3n model locally"""
    
    if model_size.lower() == "2b":
        model_id = "google/gemma-3n-E2B-it"
        model_name = "gemma3n-2b"
    elif model_size.lower() == "4b":
        model_id = "google/gemma-3n-E4B-it"
        model_name = "gemma3n-4b"
    else:
        raise ValueError("Model size must be '2b' or '4b'")
    
    if local_dir is None:
        local_dir = f"./models/{model_name}"
    
    print(f"📥 Downloading {model_id} to {local_dir}...")
    print(f"🎯 Model: Gemma 3n {model_size.upper()}")
    
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
        model = AutoModelForImageTextToText.from_pretrained(
            local_dir,
            torch_dtype=torch.float16,  # Use float16 for efficiency
            device_map="auto",          # Auto-detect best device
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        print("✅ Model loaded successfully!")
        print(f"🎯 This {model_size.upper()} model has full audio, image, and video capabilities")
        
        # Get model size
        total_params = sum(p.numel() for p in model.parameters())
        print(f"📊 Model parameters: {total_params:,}")
        
        return local_dir
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return None

def check_disk_space(required_gb: float) -> bool:
    """Check if enough disk space is available"""
    import shutil
    
    total, used, free = shutil.disk_usage("./models")
    free_gb = free / (1024**3)
    
    print(f"💾 Disk space check:")
    print(f"   Available: {free_gb:.1f}GB")
    print(f"   Required: {required_gb:.1f}GB")
    
    if free_gb < required_gb:
        print(f"❌ Insufficient disk space!")
        return False
    else:
        print(f"✅ Sufficient disk space available")
        return True

def estimate_model_size(model_size: str) -> float:
    """Estimate model size in GB"""
    if model_size.lower() == "2b":
        return 4.0  # ~4GB for 2B model
    elif model_size.lower() == "4b":
        return 8.0  # ~8GB for 4B model
    else:
        return 6.0  # Default estimate

def main():
    parser = argparse.ArgumentParser(description="Download Gemma 3n models for Jetson")
    parser.add_argument("--model", choices=["2b", "4b", "both"], default="2b",
                       help="Which model to download (2b, 4b, or both)")
    parser.add_argument("--check-space", action="store_true",
                       help="Check disk space before downloading")
    parser.add_argument("--test-load", action="store_true",
                       help="Test model loading after download")
    
    args = parser.parse_args()
    
    print("🚀 Gemma 3n Model Downloader for Jetson")
    print("=" * 50)
    
    if args.model == "both":
        models_to_download = ["2b", "4b"]
        total_required = estimate_model_size("2b") + estimate_model_size("4b")
    else:
        models_to_download = [args.model]
        total_required = estimate_model_size(args.model)
    
    # Check disk space if requested
    if args.check_space:
        if not check_disk_space(total_required):
            print("❌ Cannot proceed without sufficient disk space")
            return
    
    # Download models
    downloaded_models = []
    
    for model_size in models_to_download:
        print(f"\n📥 Downloading {model_size.upper()} model...")
        model_path = download_gemma_model(model_size)
        
        if model_path:
            downloaded_models.append((model_size, model_path))
            print(f"✅ {model_size.upper()} model downloaded successfully!")
        else:
            print(f"❌ Failed to download {model_size.upper()} model")
    
    # Summary
    print(f"\n📋 Download Summary:")
    print(f"   Models requested: {args.model.upper()}")
    print(f"   Models downloaded: {len(downloaded_models)}")
    
    for model_size, model_path in downloaded_models:
        print(f"   ✅ {model_size.upper()}: {model_path}")
    
    if downloaded_models:
        print(f"\n🎯 Next steps:")
        print(f"   1. Update your model configuration to use the downloaded models")
        print(f"   2. Test the models with: python3 scripts/test_setup.py")
        print(f"   3. Run load monitoring: python3 scripts/jetson_load_monitor.py")
        
        if len(downloaded_models) == 2:
            print(f"\n💡 Dual Model Setup:")
            print(f"   - Use 2B for quick tasks and high load")
            print(f"   - Use 4B for complex tasks and low load")
            print(f"   - Let the load monitor choose automatically")
    else:
        print(f"\n❌ No models were downloaded successfully")

if __name__ == "__main__":
    main() 