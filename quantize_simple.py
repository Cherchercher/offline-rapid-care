#!/usr/bin/env python3
"""
Simple quantization using PyTorch's built-in methods
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import os
import gc
import time

def quantize_with_pytorch():
    """Quantize using PyTorch's built-in quantization"""
    
    local_model_path = "./models/gemma3n-local"
    quantized_path = "./models/gemma3n-local-pytorch-quantized"
    
    print("📥 Loading original model for PyTorch quantization...")
    
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
    
    print("🔄 Applying PyTorch quantization...")
    
    # Prepare model for quantization
    model.eval()
    
    # Quantize the model using PyTorch's dynamic quantization
    quantized_model = torch.quantization.quantize_dynamic(
        model, 
        {torch.nn.Linear}, 
        dtype=torch.qint8
    )
    
    print("💾 Saving quantized model...")
    
    # Save quantized model
    quantized_model.save_pretrained(quantized_path)
    processor.save_pretrained(quantized_path)
    
    print(f"✅ PyTorch quantized model saved to {quantized_path}")
    return quantized_path

def quantize_weights_only():
    """Quantize only the weight matrices to reduce size"""
    
    local_model_path = "./models/gemma3n-local"
    quantized_path = "./models/gemma3n-local-weights-quantized"
    
    print("📥 Loading original model for weight quantization...")
    
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
    
    print("🔄 Quantizing weight matrices...")
    
    # Quantize linear layers
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear):
            # Quantize weights to int8
            if hasattr(module, 'weight') and module.weight is not None:
                # Get weight data
                weight_data = module.weight.data
                
                # Calculate scale for quantization
                max_val = weight_data.abs().max()
                scale = max_val / 127.0
                
                # Quantize to int8
                quantized_weight = torch.round(weight_data / scale).clamp(-127, 127).to(torch.int8)
                
                # Store original scale for dequantization
                module.register_buffer('weight_scale', torch.tensor(scale))
                module.weight.data = quantized_weight.float()  # Convert back to float for compatibility
    
    print("💾 Saving weight-quantized model...")
    
    # Save quantized model
    model.save_pretrained(quantized_path)
    processor.save_pretrained(quantized_path)
    
    print(f"✅ Weight-quantized model saved to {quantized_path}")
    return quantized_path

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

def test_quantized_model(quantized_path):
    """Test the quantized model"""
    
    if not os.path.exists(quantized_path):
        print("❌ Quantized model not found.")
        return False
    
    print("🧪 Testing quantized model...")
    
    try:
        # Load quantized model
        processor = AutoProcessor.from_pretrained(
            quantized_path,
            trust_remote_code=True
        )
        
        model = AutoModelForImageTextToText.from_pretrained(
            quantized_path,
            torch_dtype=torch.float16,
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        print("✅ Quantized model loads successfully!")
        
        # Test with simple text
        test_input = "Hello, how are you?"
        inputs = processor(
            test_input,
            return_tensors="pt",
            max_length=512,
            truncation=True
        )
        
        with torch.no_grad():
            start_time = time.time()
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                do_sample=True,
                temperature=0.1,
                pad_token_id=processor.tokenizer.pad_token_id,
                eos_token_id=processor.tokenizer.eos_token_id
            )
            generation_time = time.time() - start_time
        
        response = processor.batch_decode(outputs, skip_special_tokens=True)[0]
        print(f"✅ Test generation successful! ({generation_time:.2f}s)")
        print(f"   Input: {test_input}")
        print(f"   Output: {response}")
        
        del model
        gc.collect()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing quantized model: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting simple PyTorch quantization for Gemma 3n...")
    
    try:
        # Try PyTorch quantization first
        print("🔄 Method 1: PyTorch dynamic quantization...")
        quantized_path = quantize_with_pytorch()
        
        if not quantized_path or not os.path.exists(quantized_path):
            print("🔄 Method 2: Weight-only quantization...")
            quantized_path = quantize_weights_only()
        
        if quantized_path and os.path.exists(quantized_path):
            # Calculate size reduction
            original_size = get_folder_size("./models/gemma3n-local")
            quantized_size = get_folder_size(quantized_path)
            reduction = ((original_size - quantized_size) / original_size) * 100
            
            print(f"\n📊 Quantization Results:")
            print(f"   Original: {format_size(original_size)}")
            print(f"   Quantized: {format_size(quantized_size)}")
            print(f"   Reduction: {reduction:.1f}%")
            
            print("\n🧪 Testing quantized model...")
            success = test_quantized_model(quantized_path)
            
            if success:
                print(f"\n🎉 Quantization successful!")
                print(f"💡 The quantized model should work on Jetson Nano.")
                print(f"📁 Model saved to: {quantized_path}")
            else:
                print(f"\n⚠️ Quantization completed but testing failed.")
                
        else:
            print(f"\n❌ Quantization failed.")
            
    except Exception as e:
        print(f"\n❌ Quantization failed: {e}")
        print(f"💡 The model may need to be used without quantization.") 