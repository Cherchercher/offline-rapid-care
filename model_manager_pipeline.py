import torch
from transformers import pipeline, AutoProcessor, AutoModelForImageTextToText
import requests
from PIL import Image
from io import BytesIO
import json
from typing import Dict, List, Optional
import time
import os

class ModelManagerPipeline:
    """Model manager using Hugging Face pipeline for image-text-to-text tasks"""
    
    def __init__(self, model_path: str = "./models/gemma3n-local", device: str = "cpu"):
        """
        Initialize pipeline-based model manager
        
        Args:
            model_path: Path to local model or Hugging Face model name
            device: Device to run on ("cpu", "cuda:0", etc.)
        """
        self.model_path = model_path
        self.device = device
        self.image_pipeline = None
        self.text_pipeline = None
        self._image_model_loaded = False
        self._text_model_loaded = False
        
    def _load_image_pipeline(self):
        """Load the image-text-to-text pipeline lazily on first use"""
        if self._image_model_loaded:
            return
            
        print("🔄 Loading Gemma 3n image-text pipeline...")
        
        try:
            # Create pipeline for image-text-to-text
            self.image_pipeline = pipeline(
                task="image-text-to-text",
                model=self.model_path,
                device=self.device,
                torch_dtype=torch.float16 if self.device == "cpu" else torch.bfloat16
            )
            
            self._image_model_loaded = True
            print("✅ Image pipeline loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading image pipeline: {e}")
            raise
    
    def _load_text_pipeline(self):
        """Load the text-generation pipeline lazily on first use"""
        if self._text_model_loaded:
            return
            
        print("🔄 Loading Gemma 3n text-generation pipeline...")
        
        try:
            # Create pipeline for text-generation
            self.text_pipeline = pipeline(
                task="text-generation",
                model=self.model_path,
                device=self.device,
                torch_dtype=torch.float16 if self.device == "cpu" else torch.bfloat16
            )
            
            self._text_model_loaded = True
            print("✅ Text pipeline loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading text pipeline: {e}")
            raise
    
    def _load_image_from_url(self, url: str) -> Optional[Image.Image]:
        """Load image from URL"""
        try:
            print(f"🔊 Loading image from URL: {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGB")
            print(f"🔊 Successfully loaded image: {img.size}")
            return img
        except Exception as e:
            print(f"🔊 Error loading image from URL {url}: {e}")
            return None
    
    def chat_text(self, messages: List[Dict]) -> Dict:
        """
        Send text-only chat request using text-generation pipeline
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Load text pipeline if not already loaded
            if not self._text_model_loaded:
                self._load_text_pipeline()
            print(f"🔊 Using text pipeline: {self._text_model_loaded}")
            
            print(f"🔊 Text chat request:")
            print(f"   Messages: {json.dumps(messages, indent=2)}")
            
            start_time = time.time()
            
            # Format text input for text-generation pipeline
            text_input = ""
            for msg in messages:
                if isinstance(msg.get("content"), list):
                    for item in msg["content"]:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_input += item["text"] + " "
                elif isinstance(msg.get("content"), str):
                    text_input += msg["content"] + " "
            
            text_input = text_input.strip()
            print(f"🔊 Text input: {text_input}")
            
            print(f"🔊 About to call text pipeline...")
            result = self.text_pipeline(
                text_input,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7
            )
            print(f"🔊 Text pipeline call completed")
            
            end_time = time.time()
            inference_time = end_time - start_time
            
            print(f"🔊 Text pipeline result: {result}")
            print(f"🔊 Result type: {type(result)}")
            print(f"⏱️  Text pipeline inference time: {inference_time:.2f} seconds")
            
            # Extract the generated text
            if isinstance(result, list) and len(result) > 0:
                if 'generated_text' in result[0]:
                    response_text = result[0]['generated_text']
                else:
                    response_text = str(result[0])
            elif isinstance(result, dict):
                if 'generated_text' in result:
                    response_text = result['generated_text']
                else:
                    response_text = str(result)
            else:
                response_text = str(result)
            
            response_text = response_text.strip()
            print(f"🔊 Text response: {response_text}")
            
            return {
                'success': True,
                'response': response_text,
                'mode': 'text-pipeline',
                'model': 'gemma3n-local',
                'inference_time': inference_time
            }
            
        except Exception as e:
            import traceback
            print(f"🔊 Text pipeline error: {e}")
            print(f"🔊 Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'mode': 'text-pipeline'
            }
    
    def chat_image(self, messages: List[Dict]) -> Dict:
        """
        Send image analysis request using image-text-to-text pipeline
        
        Args:
            messages: List of message dictionaries (images should be embedded in messages)
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Load image pipeline if not already loaded
            if not self._image_model_loaded:
                self._load_image_pipeline()
            print(f"🔊 Using image pipeline: {self._image_model_loaded}")
            
            print(f"🔊 Image chat request:")
            print(f"   Messages: {json.dumps(messages, indent=2)}")
            
            start_time = time.time()
            
            # Extract images from messages
            pipeline_images = []
            for msg in messages:
                if isinstance(msg.get("content"), list):
                    for item in msg["content"]:
                        if isinstance(item, dict) and item.get("type") == "image":
                            if "url" in item:
                                pil_img = self._load_image_from_url(item["url"])
                                if pil_img:
                                    pipeline_images.append(pil_img)
                            elif "path" in item:
                                pipeline_images.append(Image.open(item["path"]).convert("RGB"))
            
            # Use image pipeline
            if pipeline_images:
                print(f"🔊 Using image pipeline with {len(pipeline_images)} images")
                
                # For single image, use the proper chat format
                if len(pipeline_images) == 1:
                    print(f"🔊 Creating chat format for single image...")
                    # Create proper chat format with image
                    chat_messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image", "image": pipeline_images[0]},
                                {"type": "text", "text": "Analyze this image for medical triage assessment."}
                            ]
                        }
                    ]
                    
                    print(f"🔊 Calling image pipeline with chat_messages...")
                    result = self.image_pipeline(
                        text=chat_messages,
                        max_new_tokens=256,
                        return_full_text=False
                    )
                    print(f"🔊 Image pipeline call completed")
                else:
                    # Multiple images - use messages format
                    result = self.image_pipeline(
                        text=messages,
                        max_new_tokens=256,
                        return_full_text=False
                    )
            else:
                return {
                    'success': False,
                    'error': 'No images found in messages for image analysis',
                    'mode': 'image-pipeline'
                }
            
            end_time = time.time()
            inference_time = end_time - start_time
            
            print(f"🔊 Image pipeline result: {result}")
            print(f"🔊 Result type: {type(result)}")
            print(f"⏱️  Image pipeline inference time: {inference_time:.2f} seconds")
            
            # Extract the generated text
            if isinstance(result, list) and len(result) > 0:
                if 'generated_text' in result[0]:
                    response_text = result[0]['generated_text']
                else:
                    response_text = str(result[0])
            elif isinstance(result, dict):
                if 'generated_text' in result:
                    response_text = result['generated_text']
                else:
                    response_text = str(result)
            else:
                response_text = str(result)
            
            # Clean up the response
            if '<start_of_image>' in response_text:
                response_text = response_text.split('<start_of_image>')[-1]
            if '<image_soft_token>' in response_text:
                response_text = response_text.split('<image_soft_token>')[-1]
            
            response_text = response_text.strip()
            print(f"🔊 Image response: {response_text}")
            
            return {
                'success': True,
                'response': response_text,
                'mode': 'image-pipeline',
                'model': 'gemma3n-local',
                'inference_time': inference_time
            }
            
        except Exception as e:
            import traceback
            print(f"🔊 Image pipeline error: {e}")
            print(f"🔊 Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'mode': 'image-pipeline'
            }
    
    def chat_video(self, messages: List[Dict]) -> Dict:
        """
        Send video analysis request (placeholder for future implementation)
        
        Args:
            messages: List of message dictionaries (video path should be embedded in messages)
        
        Returns:
            Dictionary with response and metadata
        """
        return {
            'success': False,
            'error': 'Video analysis not yet implemented',
            'mode': 'video-pipeline'
        }
    
    def chat_audio(self, messages: List[Dict]) -> Dict:
        """
        Send audio transcription request using direct model loading (like old implementation)
        
        Args:
            messages: List of message dictionaries (audio path should be embedded in messages)
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            print(f"🔊 Audio chat request:")
            print(f"   Messages: {json.dumps(messages, indent=2)}")
            
            start_time = time.time()
            
            # Use the same approach as the old model_manager.py
            # Load model and processor directly (not pipeline)
            if not hasattr(self, 'direct_model') or not hasattr(self, 'direct_processor'):
                print("🔄 Loading direct model for audio transcription...")
                self._load_direct_model()
            
            if not self.direct_model or not self.direct_processor:
                raise Exception("Direct model not loaded")
            
            print(f"🔊 Using direct model for audio transcription")
            
            # Apply chat template (same as old implementation)
            input_ids = self.direct_processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            
            # Move to CPU with the same dtype as the model
            model_dtype = next(self.direct_model.parameters()).dtype
            input_ids = input_ids.to("cpu", dtype=model_dtype)
            print(f"🔊 Using model dtype: {model_dtype}")
            
            # Generate response
            outputs = self.direct_model.generate(
                **input_ids, 
                max_new_tokens=512,  # Longer for audio transcription
                do_sample=True,
                temperature=0.7
            )
            
            # Decode response
            decoded_outputs = self.direct_processor.batch_decode(
                outputs,
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False
            )
            
            if isinstance(decoded_outputs, list) and len(decoded_outputs) > 0:
                response_text = decoded_outputs[0]
            else:
                response_text = str(decoded_outputs)
            
            # Extract just the model's response (after <start_of_turn>model)
            if '<start_of_turn>model' in response_text:
                model_response = response_text.split('<start_of_turn>model')[-1]
                if '<end_of_turn>' in model_response:
                    model_response = model_response.split('<end_of_turn>')[0]
                # Clean up any remaining special tokens
                model_response = model_response.replace('<bos>', '').replace('<eos>', '').strip()
            else:
                model_response = response_text
            
            end_time = time.time()
            inference_time = end_time - start_time
            
            print(f"🔊 Audio response: {model_response}")
            print(f"⏱️  Audio transcription time: {inference_time:.2f} seconds")
            
            return {
                'success': True,
                'response': model_response,
                'mode': 'audio-direct',
                'model': 'gemma3n-local',
                'inference_time': inference_time
            }
            
        except Exception as e:
            import traceback
            print(f"🔊 Audio transcription error: {e}")
            print(f"🔊 Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'mode': 'audio-direct'
            }
    
    def _load_direct_model(self):
        """Load model directly using transformers (like old implementation)"""
        try:
            print("📥 Loading Gemma 3n model directly for audio...")
            
            # Use local model path
            local_model_path = "./models/gemma3n-local"
            
            # Check if local model exists
            if not os.path.exists(local_model_path):
                print(f"❌ Local model not found at {local_model_path}")
                raise FileNotFoundError(f"Local model not found at {local_model_path}")
            
            # Load processor and model from local directory
            self.direct_processor = AutoProcessor.from_pretrained(
                local_model_path, 
                trust_remote_code=True
            )
            
            # Load model with auto dtype
            self.direct_model = AutoModelForImageTextToText.from_pretrained(
                local_model_path, 
                torch_dtype="auto", 
                device_map="cpu",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            print("✅ Direct model loaded successfully for audio")
            
        except Exception as e:
            print(f"❌ Failed to load direct model: {e}")
            raise
    
    def get_status(self) -> Dict:
        """Get current model status"""
        return {
            'mode': 'pipeline',
            'model_path': self.model_path,
            'device': self.device,
            'image_pipeline_loaded': self._image_model_loaded,
            'text_pipeline_loaded': self._text_model_loaded
        }

# Global instance
_pipeline_manager = None

def get_pipeline_manager() -> ModelManagerPipeline:
    """Get global pipeline manager instance"""
    global _pipeline_manager
    if _pipeline_manager is None:
        _pipeline_manager = ModelManagerPipeline()
    return _pipeline_manager 