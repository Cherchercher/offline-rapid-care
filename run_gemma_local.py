#!/usr/bin/env python3
"""
Run Gemma 3n model locally for audio transcription and multimodal tasks
"""

import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import os
import requests
from pathlib import Path

# Use local model path
LOCAL_MODEL_PATH = "./models/gemma3n-local"

def download_audio_file(url, local_path):
    """Download audio file from URL to local path"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def run_gemma_local():
    """Run Gemma 3n model locally with audio transcription"""
    
    print("Loading Gemma 3n model from local directory...")
    
    # Load processor and model from local directory
    processor = AutoProcessor.from_pretrained(
        LOCAL_MODEL_PATH, 
        device_map="cpu",
        trust_remote_code=True
    )
    
    model = AutoModelForImageTextToText.from_pretrained(
        LOCAL_MODEL_PATH, 
        torch_dtype=torch.float32, 
        device_map="cpu",
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    
    print("Model loaded successfully on CPU")
    
    # Example 1: Text-only conversation
    print("\n=== Example 1: Text-only conversation ===")
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
        input_ids = input_ids.to("cpu", dtype=torch.float32)
        
        outputs = model.generate(**input_ids, max_new_tokens=64)
        
        text = processor.batch_decode(
            outputs,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False
        )
        print("Response:", text[0])
    except Exception as e:
        print(f"Error with text-only example: {e}")
    
    # Example 2: Audio transcription (if audio files exist)
    print("\n=== Example 2: Audio transcription ===")
    
    # Check if we have audio files in uploads directory
    uploads_dir = Path("./uploads")
    audio_files = []
    
    if uploads_dir.exists():
        for audio_file in uploads_dir.glob("*.wav"):
            audio_files.append(str(audio_file))
        for audio_file in uploads_dir.glob("*.mp3"):
            audio_files.append(str(audio_file))
        for audio_file in uploads_dir.glob("*.m4a"):
            audio_files.append(str(audio_file))
    
    if audio_files:
        print(f"Found {len(audio_files)} audio files: {audio_files[:3]}...")
        
        # Create messages with local audio file paths
        audio_messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe these audio files in order:"}
                ]
            }
        ]
        
        # Add audio files to the message
        for audio_file in audio_files[:3]:  # Limit to first 3 files
            audio_messages[0]["content"].append({
                "type": "audio", 
                "audio": audio_file
            })
        
        try:
            input_ids = processor.apply_chat_template(
                audio_messages,
                add_generation_prompt=True,
                tokenize=True, 
                return_dict=True,
                return_tensors="pt",
            )
            input_ids = input_ids.to("cpu", dtype=torch.float32)
            
            outputs = model.generate(**input_ids, max_new_tokens=256)
            
            text = processor.batch_decode(
                outputs,
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False
            )
            print("Audio transcription response:", text[0])
        except Exception as e:
            print(f"Error with audio transcription: {e}")
    else:
        print("No audio files found in ./uploads directory")
        print("You can add audio files to ./uploads/ and run this script again")
    
    # Example 3: Interactive mode
    print("\n=== Example 3: Interactive mode ===")
    print("Type 'quit' to exit")
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_input}
                    ]
                }
            ]
            
            input_ids = processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True, 
                return_dict=True,
                return_tensors="pt",
            )
            input_ids = input_ids.to("cpu", dtype=torch.float32)
            
            outputs = model.generate(**input_ids, max_new_tokens=128)
            
            text = processor.batch_decode(
                outputs,
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False
            )
            print("Gemma:", text[0])
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_gemma_local() 