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
    """Model manager using direct model loading for all tasks"""
    
    def __init__(self, model_path: str = "./models/gemma3n-local", device: str = "cpu"):
        """
        Initialize direct model manager
        
        Args:
            model_path: Path to local model or Hugging Face model name
            device: Device to run on ("cpu", "cuda:0", etc.)
        """
        self.model_path = model_path
        self.device = device
        self.direct_model = None
        self.direct_processor = None
        self._model_loaded = False
        
    def _load_direct_model(self):
        """Load model directly using transformers (lazily on first use)"""
        if self._model_loaded:
            return
            
        print("🔄 Loading Gemma 3n model directly...")
        
        try:
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
            
            self._model_loaded = True
            print("✅ Direct model loaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to load direct model: {e}")
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
        Send text-only chat request using direct model loading
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Load model if not already loaded
            if not self._model_loaded:
                self._load_direct_model()
            
            if not self.direct_model or not self.direct_processor:
                raise Exception("Direct model not loaded")
            
            print(f"🔊 Using direct model for text")
            print(f"🔊 Text chat request:")
            print(f"   Messages: {json.dumps(messages, indent=2)}")
            
            start_time = time.time()
            
            # Apply chat template
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
                max_new_tokens=256,
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
            
            print(f"🔊 Text response: {model_response}")
            print(f"⏱️  Text inference time: {inference_time:.2f} seconds")
            
            return {
                'success': True,
                'response': model_response,
                'mode': 'text-direct',
                'model': 'gemma3n-local',
                'inference_time': inference_time
            }
            
        except Exception as e:
            import traceback
            print(f"🔊 Text inference error: {e}")
            print(f"🔊 Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'mode': 'text-direct'
            }
    
    def chat_image(self, messages: List[Dict]) -> Dict:
        """
        Send image analysis request using direct model loading
        
        Args:
            messages: List of message dictionaries (images should be embedded in messages)
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Load model if not already loaded
            if not self._model_loaded:
                self._load_direct_model()
            
            if not self.direct_model or not self.direct_processor:
                raise Exception("Direct model not loaded")
            
            print(f"🔊 Using direct model for image analysis")
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
            
            # Apply chat template with or without images
            if pipeline_images:
                print(f"🔊 Using {len(pipeline_images)} images with chat template")
                input_ids = self.direct_processor.apply_chat_template(
                    messages,
                    images=pipeline_images,
                    add_generation_prompt=True,
                    tokenize=True,
                    return_dict=True,
                    return_tensors="pt"
                )
            else:
                print(f"🔊 No images found, using text-only chat template")
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
                max_new_tokens=256,
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
            
            print(f"🔊 Image response: {model_response}")
            print(f"⏱️  Image inference time: {inference_time:.2f} seconds")
            
            return {
                'success': True,
                'response': model_response,
                'mode': 'image-direct',
                'model': 'gemma3n-local',
                'inference_time': inference_time
            }
            
        except Exception as e:
            import traceback
            print(f"🔊 Image inference error: {e}")
            print(f"🔊 Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'mode': 'image-direct'
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
        Send audio transcription request using direct model loading
        
        Args:
            messages: List of message dictionaries (audio path should be embedded in messages)
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Load model if not already loaded
            if not self._model_loaded:
                self._load_direct_model()
            
            if not self.direct_model or not self.direct_processor:
                raise Exception("Direct model not loaded")
            
            print(f"🔊 Using direct model for audio transcription")
            print(f"🔊 Audio chat request:")
            print(f"   Messages: {json.dumps(messages, indent=2)}")
            
            start_time = time.time()
            
            # Apply chat template
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
    
    def get_status(self) -> Dict:
        """Get current model status"""
        return {
            'mode': 'direct',
            'model_path': self.model_path,
            'device': self.device,
            'model_loaded': self._model_loaded,
            'direct_model_loaded': self.direct_model is not None,
            'direct_processor_loaded': self.direct_processor is not None
        }

# Global instance
_pipeline_manager = None

def get_pipeline_manager() -> ModelManagerPipeline:
    """Get global pipeline manager instance"""
    global _pipeline_manager
    if _pipeline_manager is None:
        _pipeline_manager = ModelManagerPipeline()
    return _pipeline_manager 