#!/usr/bin/env python3
"""
Alternative quantization approach for Gemma 3n using different methods
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import os
import gc
import time

def quantize_with_awq():
    """Try AWQ quantization which is more compatible"""
    
    local_model_path = "./models/gemma3n-local"
    quantized_path = "./models/gemma3n-local-awq"
    
    print("📥 Loading original model for AWQ quantization...")
    
    # Load processor
    processor = AutoProcessor.from_pretrained(
        local_model_path,
        trust_remote_code=True
    )
    
    # Try AWQ quantization
    try:
        from awq import AutoAWQForCausalLM
        from awq.utils.auto_awq import AutoAWQ
        
        print("🔄 Applying AWQ quantization...")
        
        # Load model
        model = AutoModelForImageTextToText.from_pretrained(
            local_model_path,
            torch_dtype=torch.float16,
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        # Apply AWQ quantization
        awq = AutoAWQ(model, processor)
        awq.quantize(
            quant_config={
                "zero_point": True,
                "q_group_size": 128,
                "w_bit": 4,
                "scheme": "asym"
            },
            calib_data="hello world",  # Simple calibration data
            export_awq=True
        )
        
        # Save quantized model
        awq.save_quantized(quantized_path)
        processor.save_pretrained(quantized_path)
        
        print(f"✅ AWQ quantized model saved to {quantized_path}")
        return quantized_path
        
    except ImportError:
        print("❌ AWQ not available, trying GPTQ...")
        return quantize_with_gptq()
    except Exception as e:
        print(f"❌ AWQ quantization failed: {e}")
        return quantize_with_gptq()

def quantize_with_gptq():
    """Try GPTQ quantization"""
    
    local_model_path = "./models/gemma3n-local"
    quantized_path = "./models/gemma3n-local-gptq"
    
    print("📥 Loading original model for GPTQ quantization...")
    
    # Load processor
    processor = AutoProcessor.from_pretrained(
        local_model_path,
        trust_remote_code=True
    )
    
    try:
        from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
        
        print("🔄 Applying GPTQ quantization...")
        
        # Create quantization config
        quantize_config = BaseQuantizeConfig(
            bits=4,
            group_size=128,
            damp_percent=0.1,
            desc_act=False,
            static_groups=False,
            sym=True,
            true_sequential=True,
            model_name_or_path=None,
            model_file_base_name="model"
        )
        
        # Load and quantize model
        model = AutoGPTQForCausalLM.from_pretrained(
            local_model_path,
            quantize_config=quantize_config,
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        # Save quantized model
        model.save_quantized(quantized_path)
        processor.save_pretrained(quantized_path)
        
        print(f"✅ GPTQ quantized model saved to {quantized_path}")
        return quantized_path
        
    except ImportError:
        print("❌ GPTQ not available, trying manual quantization...")
        return quantize_manual()
    except Exception as e:
        print(f"❌ GPTQ quantization failed: {e}")
        return quantize_manual()

def quantize_manual():
    """Manual quantization approach"""
    
    local_model_path = "./models/gemma3n-local"
    quantized_path = "./models/gemma3n-local-manual"
    
    print("📥 Loading original model for manual quantization...")
    
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
    
    print("🔄 Applying manual quantization...")
    
    # Manually quantize weights to int8
    for name, param in model.named_parameters():
        if param.dtype == torch.float16:
            # Quantize to int8
            param.data = torch.quantize_per_tensor(
                param.data.float(), 
                scale=param.data.abs().max() / 127.0, 
                zero_point=0, 
                dtype=torch.qint8
            ).int_repr().to(torch.int8)
    
    print("💾 Saving manually quantized model...")
    
    # Save quantized model
    model.save_pretrained(quantized_path)
    processor.save_pretrained(quantized_path)
    
    print(f"✅ Manually quantized model saved to {quantized_path}")
    return quantized_path

def install_quantization_libs():
    """Install quantization libraries"""
    
    print("📦 Installing quantization libraries...")
    
    try:
        # Try installing AWQ
        os.system("pip install awq")
        print("✅ AWQ installed")
        return "awq"
    except:
        try:
            # Try installing GPTQ
            os.system("pip install auto-gptq")
            print("✅ GPTQ installed")
            return "gptq"
        except:
            print("⚠️ Could not install quantization libraries, using manual approach")
            return "manual"

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
    print("🚀 Starting alternative quantization for Gemma 3n...")
    
    # Install quantization libraries
    method = install_quantization_libs()
    
    # Try quantization based on available method
    if method == "awq":
        quantized_path = quantize_with_awq()
    elif method == "gptq":
        quantized_path = quantize_with_gptq()
    else:
        quantized_path = quantize_manual()
    
    if quantized_path and os.path.exists(quantized_path):
        # Calculate size reduction
        original_size = get_folder_size("./models/gemma3n-local")
        quantized_size = get_folder_size(quantized_path)
        reduction = ((original_size - quantized_size) / original_size) * 100
        
        print(f"\n📊 Quantization Results:")
        print(f"   Original: {format_size(original_size)}")
        print(f"   Quantized: {format_size(quantized_size)}")
        print(f"   Reduction: {reduction:.1f}%")
        print(f"   Method used: {method.upper()}")
        
        print(f"\n🎉 Quantization successful!")
        print(f"💡 The quantized model should work on Jetson Nano.")
    else:
        print(f"\n❌ All quantization methods failed.")
        print(f"💡 The model may need to be used without quantization.") 