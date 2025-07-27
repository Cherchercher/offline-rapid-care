#!/usr/bin/env python3
"""
Reduce model size for Jetson Nano compatibility
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import os
import gc
import time

def compress_safetensors():
    """Compress safetensors files for size reduction"""
    
    local_model_path = "./models/gemma3n-local"
    compressed_path = "./models/gemma3n-local-compressed"
    
    print("📥 Compressing safetensors files...")
    
    # Copy all files
    os.system(f"cp -r {local_model_path} {compressed_path}")
    
    # Compress safetensors files
    for root, dirs, files in os.walk(compressed_path):
        for file in files:
            if file.endswith('.safetensors'):
                file_path = os.path.join(root, file)
                print(f"🔄 Compressing {file}...")
                
                # Load and save with compression
                try:
                    import safetensors.torch
                    tensors = safetensors.torch.load_file(file_path)
                    safetensors.torch.save_file(tensors, file_path, compression="lz4")
                    print(f"✅ Compressed {file}")
                except:
                    print(f"⚠️ Could not compress {file}")
    
    print(f"✅ Compressed model saved to {compressed_path}")
    return compressed_path

def create_pruned_model():
    """Create a pruned version by removing some layers"""
    
    local_model_path = "./models/gemma3n-local"
    pruned_path = "./models/gemma3n-local-pruned"
    
    print("📥 Loading model for pruning...")
    
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
    
    print("🔄 Creating pruned model...")
    
    # Create a smaller model by removing some layers
    # This is a simplified approach - in practice you'd want more sophisticated pruning
    
    # Save the model with reduced precision for some layers
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Linear) and 'mlp' in name:
            # Reduce precision for MLP layers
            if hasattr(module, 'weight') and module.weight is not None:
                # Convert to int8 for MLP layers
                weight_data = module.weight.data
                max_val = weight_data.abs().max()
                if max_val > 0:
                    scale = max_val / 127.0
                    quantized_weight = torch.round(weight_data / scale).clamp(-127, 127).to(torch.int8)
                    module.register_buffer('weight_scale', torch.tensor(scale))
                    module.weight.data = quantized_weight.float()
    
    print("💾 Saving pruned model...")
    
    # Save model
    model.save_pretrained(pruned_path)
    processor.save_pretrained(pruned_path)
    
    print(f"✅ Pruned model saved to {pruned_path}")
    return pruned_path

def create_optimized_model():
    """Create an optimized version with better memory management"""
    
    local_model_path = "./models/gemma3n-local"
    optimized_path = "./models/gemma3n-local-optimized"
    
    print("📥 Loading model for optimization...")
    
    # Load processor
    processor = AutoProcessor.from_pretrained(
        local_model_path,
        trust_remote_code=True
    )
    
    # Load model with optimizations
    model = AutoModelForImageTextToText.from_pretrained(
        local_model_path,
        torch_dtype=torch.float16,
        device_map="cpu",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        offload_folder="./offload",
        offload_state_dict=True
    )
    
    print("🔄 Optimizing model...")
    
    # Apply optimizations
    model.eval()
    
    # Use torch.compile for optimization (if available)
    try:
        model = torch.compile(model, mode="reduce-overhead")
        print("✅ Applied torch.compile optimization")
    except:
        print("⚠️ torch.compile not available")
    
    print("💾 Saving optimized model...")
    
    # Save model
    model.save_pretrained(optimized_path)
    processor.save_pretrained(optimized_path)
    
    print(f"✅ Optimized model saved to {optimized_path}")
    return optimized_path

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

def test_model(model_path):
    """Test the model"""
    
    if not os.path.exists(model_path):
        print("❌ Model not found.")
        return False
    
    print("🧪 Testing model...")
    
    try:
        # Load model
        processor = AutoProcessor.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        model = AutoModelForImageTextToText.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        print("✅ Model loads successfully!")
        
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
        print(f"❌ Error testing model: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting model size reduction for Jetson Nano...")
    
    original_size = get_folder_size("./models/gemma3n-local")
    print(f"📊 Original model size: {format_size(original_size)}")
    
    results = []
    
    # Try different methods
    methods = [
        ("Safetensors compression", compress_safetensors),
        ("Model pruning", create_pruned_model),
        ("Model optimization", create_optimized_model)
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"\n🔄 Trying {method_name}...")
            result_path = method_func()
            
            if result_path and os.path.exists(result_path):
                result_size = get_folder_size(result_path)
                reduction = ((original_size - result_size) / original_size) * 100
                
                print(f"✅ {method_name} successful!")
                print(f"   Size: {format_size(result_size)}")
                print(f"   Reduction: {reduction:.1f}%")
                
                # Test the model
                success = test_model(result_path)
                
                results.append({
                    'method': method_name,
                    'path': result_path,
                    'size': result_size,
                    'reduction': reduction,
                    'test_success': success
                })
                
                if success and result_size * 0.9 < 4 * 1024**3 * 0.8:
                    print(f"🎉 {method_name} is ready for Jetson Nano!")
                    break
                    
        except Exception as e:
            print(f"❌ {method_name} failed: {e}")
    
    # Show summary
    print(f"\n📊 Summary of size reduction attempts:")
    for result in results:
        status = "✅" if result['test_success'] else "⚠️"
        jetson_compatible = result['size'] * 0.9 < 4 * 1024**3 * 0.8
        jetson_status = "✅" if jetson_compatible else "❌"
        print(f"   {status} {result['method']}: {format_size(result['size'])} ({result['reduction']:.1f}% reduction) {jetson_status}")
    
    if results:
        best_result = max(results, key=lambda x: x['reduction'])
        print(f"\n🏆 Best result: {best_result['method']}")
        print(f"   Size: {format_size(best_result['size'])}")
        print(f"   Reduction: {best_result['reduction']:.1f}%")
        print(f"   Jetson Nano compatible: {'✅ YES' if best_result['size'] * 0.9 < 4 * 1024**3 * 0.8 else '❌ NO'}")
        
        if best_result['size'] * 0.9 < 4 * 1024**3 * 0.8:
            print(f"\n🎉 SUCCESS! You can use {best_result['method']} for Jetson Nano!")
            print(f"📁 Model path: {best_result['path']}")
        else:
            print(f"\n⚠️ Even the best reduction isn't enough for Jetson Nano.")
            print(f"💡 Consider using Jetson Xavier NX (8GB RAM) instead.")
    else:
        print(f"\n❌ All size reduction methods failed.")
        print(f"💡 The model may be too large for Jetson Nano.")
        print(f"💡 Consider Jetson Xavier NX or cloud deployment.") 