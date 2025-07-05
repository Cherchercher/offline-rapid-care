#!/usr/bin/env python3
"""
Run Gemma 3n model with offloading to reduce memory usage
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import os
from pathlib import Path

# Use local model path
LOCAL_MODEL_PATH = "./models/gemma3n-local"

def run_gemma_with_offload():
    """Run Gemma 3n model with offloading for lower memory usage"""
    
    print("Loading Gemma 3n model with offloading...")
    
    # Load processor
    processor = AutoProcessor.from_pretrained(
        LOCAL_MODEL_PATH, 
        trust_remote_code=True
    )
    
    # Load model with offloading
    model = AutoModelForImageTextToText.from_pretrained(
        LOCAL_MODEL_PATH, 
        torch_dtype=torch.float16,  # Use half precision
        device_map="auto",  # Let transformers decide device mapping
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        offload_folder="./offload",  # Offload to disk
        offload_state_dict=True
    )
    
    print("Model loaded successfully with offloading")
    
    # Test the model
    print("\n=== Testing model ===")
    text_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Hello! How are you today?"}
            ]
        }
    ]
    
    try:
        input_ids = processor.apply_chat_template(
            text_messages,
            add_generation_prompt=True,
            tokenize=True, 
            return_dict=True,
            return_tensors="pt",
        )
        
        # Move to appropriate device
        device = next(model.parameters()).device
        input_ids = input_ids.to(device, dtype=torch.float16)
        
        outputs = model.generate(**input_ids, max_new_tokens=64)
        
        text = processor.batch_decode(
            outputs,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False
        )
        print("Response:", text[0])
        print("✅ Model is working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing model: {e}")

if __name__ == "__main__":
    run_gemma_with_offload() 