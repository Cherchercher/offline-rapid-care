#!/usr/bin/env python3
"""
Compatible quantization script for Gemma 3n models
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig
import os
import gc
import time

def quantize_gemma_compatible():
    """Quantize Gemma 3n using a more compatible approach"""
    
    local_model_path = "./models/gemma3n-local"
    quantized_path = "./models/gemma3n-local-4bit"
    
    print("📥 Loading original model for quantization...")
    
    # Load processor
    processor = AutoProcessor.from_pretrained(
        local_model_path,
        trust_remote_code=True
    )
    
    # Create a more conservative quantization config
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=False,  # Disable double quantization
        bnb_4bit_quant_type="nf4",        # Use NormalFloat4
        llm_int8_threshold=6.0,           # Higher threshold for stability
        llm_int8_has_fp16_weight=False    # Disable fp16 weights
    )
    
    print("🔄 Loading model with quantization...")
    
    # Load model with more conservative settings
    model = AutoModelForImageTextToText.from_pretrained(
        local_model_path,
        torch_dtype=torch.float16,
        device_map="cpu",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        quantization_config=quantization_config,
        offload_folder="./offload",  # Use disk offloading
        offload_state_dict=True
    )
    
    print("💾 Saving quantized model...")
    
    # Save quantized model
    model.save_pretrained(quantized_path)
    processor.save_pretrained(quantized_path)
    
    # Clean up memory
    del model
    gc.collect()
    
    print(f"✅ Quantized model saved to {quantized_path}")
    
    # Calculate size reduction
    original_size = get_folder_size(local_model_path)
    quantized_size = get_folder_size(quantized_path)
    reduction = ((original_size - quantized_size) / original_size) * 100
    
    print(f"📊 Size comparison:")
    print(f"   Original: {format_size(original_size)}")
    print(f"   Quantized: {format_size(quantized_size)}")
    print(f"   Reduction: {reduction:.1f}%")
    
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
        
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=False,
            bnb_4bit_quant_type="nf4"
        )
        
        model = AutoModelForImageTextToText.from_pretrained(
            quantized_path,
            torch_dtype=torch.float16,
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            quantization_config=quantization_config
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
    print("🚀 Starting compatible Gemma 3n quantization...")
    
    try:
        quantized_path = quantize_gemma_compatible()
        print("\n🧪 Testing quantized model...")
        success = test_quantized_model(quantized_path)
        
        if success:
            print("\n🎉 Quantization successful!")
            print("💡 The quantized model should work on Jetson Nano.")
        else:
            print("\n⚠️ Quantization completed but testing failed.")
            print("💡 You may need to adjust settings for your specific use case.")
            
    except Exception as e:
        print(f"\n❌ Quantization failed: {e}")
        print("💡 This model may require a different quantization approach.") 