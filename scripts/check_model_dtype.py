#!/usr/bin/env python3
"""
Check the current model's dtype and size
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import os

def check_model_info():
    """Check the current model's dtype and size"""
    
    local_model_path = "./models/gemma3n-local-e2b"
    
    print("📊 Checking current model information...")
    
    # Load processor
    processor = AutoProcessor.from_pretrained(
        local_model_path,
        trust_remote_code=True
    )
    
    # Load model
    model = AutoModelForImageTextToText.from_pretrained(
        local_model_path,
        torch_dtype=torch.float16,
        device_map="cpu",
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    
    print("🔍 Analyzing model parameters...")
    
    # Check dtypes of parameters
    dtypes = {}
    total_params = 0
    
    for name, param in model.named_parameters():
        dtype = str(param.dtype)
        dtypes[dtype] = dtypes.get(dtype, 0) + param.numel()
        total_params += param.numel()
    
    print(f"📈 Parameter statistics:")
    for dtype, count in dtypes.items():
        percentage = (count / total_params) * 100
        print(f"   {dtype}: {count:,} parameters ({percentage:.1f}%)")
    
    # Check model size on disk
    model_size = get_folder_size(local_model_path)
    print(f"📁 Model size on disk: {format_size(model_size)}")
    
    # Estimate memory usage
    memory_usage = model_size * 0.9  # Rough estimate
    print(f"💾 Estimated RAM usage: {format_size(memory_usage)}")
    
    # Check Jetson Nano compatibility
    jetson_ram = 4 * 1024 * 1024 * 1024  # 4GB
    compatible = memory_usage < jetson_ram * 0.8
    
    print(f"\n🚀 Jetson Nano compatibility:")
    print(f"   Jetson Nano RAM: {format_size(jetson_ram)}")
    print(f"   Model RAM usage: {format_size(memory_usage)}")
    print(f"   Compatible: {'✅ YES' if compatible else '❌ NO'}")
    
    if not compatible:
        needed_reduction = ((memory_usage - jetson_ram * 0.8) / memory_usage) * 100
        print(f"   Needed reduction: {needed_reduction:.1f}%")
    
    return {
        'model_size': model_size,
        'memory_usage': memory_usage,
        'compatible': compatible,
        'dtypes': dtypes
    }

def get_folder_size(folder_path):
    """Get the total size of a folder in bytes"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    return total_size

def format_size(size_bytes):
    """Format bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

if __name__ == "__main__":
    info = check_model_info()
    
    print(f"\n💡 Recommendations:")
    if info['compatible']:
        print("   ✅ The model should work on Jetson Nano as-is!")
        print("   💡 No quantization needed.")
    else:
        print("   ⚠️ The model needs size reduction for Jetson Nano.")
        print("   💡 Consider quantization or compression.") 