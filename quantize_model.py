#!/usr/bin/env python3
"""
Quantize Gemma 3n model to reduce memory usage for edge devices like Jetson Nano
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import os
import gc

def quantize_model():
    """Quantize the model to 4-bit precision with Jetson Nano optimizations"""
    
    local_model_path = "./models/gemma3n-local"
    quantized_path = "./models/gemma3n-local-4bit"
    
    print("📥 Loading original model for quantization...")
    
    # Load processor
    processor = AutoProcessor.from_pretrained(
        local_model_path,
        trust_remote_code=True
    )
    
    # Load model with aggressive quantization for edge devices
    model = AutoModelForImageTextToText.from_pretrained(
        local_model_path,
        torch_dtype=torch.float16,
        device_map="cpu",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,  # Double quantization for extra compression
        bnb_4bit_quant_type="nf4"        # NormalFloat4 for better quality
    )
    
    print("💾 Saving quantized model...")
    
    # Save quantized model
    model.save_pretrained(quantized_path)
    processor.save_pretrained(quantized_path)
    
    # Clean up memory
    del model
    gc.collect()
    
    print(f"✅ Quantized model saved to {quantized_path}")
    print("💡 Update model_manager.py to use this path for lower memory usage")
    print("🚀 Optimized for Jetson Nano and other edge devices")

def create_jetson_optimized_runner():
    """Create a Jetson Nano optimized model runner"""
    
    jetson_runner_code = '''#!/usr/bin/env python3
"""
Jetson Nano optimized Gemma 3n runner
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import gc
import time

class JetsonGemmaRunner:
    def __init__(self, model_path="./models/gemma3n-local-4bit"):
        self.model_path = model_path
        self.processor = None
        self.model = None
        
    def load_model(self):
        """Load model with Jetson Nano optimizations"""
        print("🔄 Loading quantized model for Jetson Nano...")
        
        # Force CPU usage and memory optimizations
        torch.set_num_threads(4)  # Use all 4 cores
        
        self.processor = AutoProcessor.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16
        )
        
        print("✅ Model loaded successfully on Jetson Nano")
        
    def transcribe_audio(self, audio_file_path):
        """Transcribe audio with memory management"""
        if not self.model:
            self.load_model()
            
        try:
            # Load and process audio
            with open(audio_file_path, "rb") as f:
                audio_data = f.read()
            
            # Process with memory cleanup
            inputs = self.processor(
                audio_data,
                return_tensors="pt",
                sampling_rate=16000
            )
            
            # Generate with memory management
            with torch.no_grad():
                start_time = time.time()
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.1,
                    top_p=0.9,
                    pad_token_id=self.processor.tokenizer.pad_token_id,
                    eos_token_id=self.processor.tokenizer.eos_token_id
                )
                generation_time = time.time() - start_time
            
            # Decode and clean output
            transcription = self.processor.batch_decode(
                outputs, 
                skip_special_tokens=True
            )[0]
            
            # Clean up memory
            del inputs, outputs
            gc.collect()
            
            print(f"⏱️ Generation time: {generation_time:.2f}s")
            return transcription.strip()
            
        except Exception as e:
            print(f"❌ Error during transcription: {e}")
            return None

if __name__ == "__main__":
    runner = JetsonGemmaRunner()
    # Test with a sample audio file
    # result = runner.transcribe_audio("sample.wav")
    # print(f"Transcription: {result}")
'''
    
    with open("jetson_gemma_runner.py", "w") as f:
        f.write(jetson_runner_code)
    
    print("✅ Created jetson_gemma_runner.py for optimized Jetson Nano usage")

if __name__ == "__main__":
    quantize_model()
    create_jetson_optimized_runner() 