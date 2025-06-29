import os
import requests
import json
from typing import Dict, List, Optional, Union
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import numpy as np
from PIL import Image
import base64
import io

class ModelManager:
    """Manages both direct model loading and Ollama API modes"""
    
    def __init__(self, mode: str = "auto", ollama_url: str = "http://localhost:11434"):
        """
        Initialize model manager
        
        Args:
            mode: "direct", "ollama", or "auto"
            ollama_url: URL for Ollama service
        """
        self.mode = mode
        self.ollama_url = ollama_url
        self.model_name = "gemma3n:e4b"
        self.direct_model = None
        self.direct_processor = None
        self.direct_pipeline = None
        
        # Auto-detect mode if not specified
        if mode == "auto":
            self.mode = self._detect_best_mode()
        
        # Initialize based on mode
        if self.mode == "direct":
            self._load_direct_model()
        elif self.mode == "ollama":
            self._check_ollama_connection()
    
    def _detect_best_mode(self) -> str:
        """Auto-detect the best mode based on environment"""
        # Check if Ollama is available
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if any(self.model_name in model.get('name', '') for model in models):
                    print(f"✅ Ollama mode detected - {self.model_name} available")
                    return "ollama"
        except:
            pass
        
        # Fall back to direct mode
        print("🔄 Direct mode detected - loading model locally")
        return "direct"
    
    def _load_direct_model(self):
        """Load model directly using transformers"""
        try:
            print("📥 Loading Gemma 3n model directly...")
            
            # Load processor and model
            self.direct_processor = AutoProcessor.from_pretrained(
                "google/gemma-3n-E4B-it", 
                device_map="auto"
            )
            
            self.direct_model = AutoModelForImageTextToText.from_pretrained(
                "google/gemma-3n-E4B-it", 
                torch_dtype="auto", 
                device_map="auto"
            )
            
            print("✅ Direct model loaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to load direct model: {e}")
            raise
    
    def _check_ollama_connection(self):
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise Exception("Ollama service not responding")
            
            models = response.json().get('models', [])
            model_found = any(self.model_name in model.get('name', '') for model in models)
            
            if not model_found:
                print(f"⚠️  Model {self.model_name} not found in Ollama. Pulling...")
                self._pull_ollama_model()
            
            print("✅ Ollama connection verified")
            
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            print("🔄 Falling back to direct mode...")
            self.mode = "direct"
            self._load_direct_model()
    
    def _pull_ollama_model(self):
        """Pull model to Ollama"""
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "pull", self.model_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                print(f"✅ Model {self.model_name} pulled successfully")
            else:
                raise Exception(f"Failed to pull model: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Failed to pull model: {e}")
            raise
    
    def chat(self, messages: List[Dict], images: Optional[List[np.ndarray]] = None) -> Dict:
        """
        Send chat request to model
        
        Args:
            messages: List of message dictionaries
            images: Optional list of images as numpy arrays
        
        Returns:
            Dictionary with response and metadata
        """
        if self.mode == "ollama":
            return self._chat_ollama(messages, images)
        else:
            return self._chat_direct(messages, images)
    
    def _chat_ollama(self, messages: List[Dict], images: Optional[List[np.ndarray]] = None) -> Dict:
        """Chat using Ollama API with proper image handling for Gemma 3n"""
        try:
            # Prepare messages for Ollama
            ollama_messages = []
            
            for msg in messages:
                if msg['role'] == 'user':
                    # Check if message contains image URLs or base64 images
                    has_images = False
                    content_parts = []
                    
                    if isinstance(msg['content'], list):
                        # Handle multimodal content with image URLs
                        for item in msg['content']:
                            if isinstance(item, dict):
                                if item.get('type') == 'image' and item.get('url'):
                                    # Use image URL directly
                                    content_parts.append({
                                        "type": "image",
                                        "url": item['url']
                                    })
                                    has_images = True
                                elif item.get('type') == 'text':
                                    content_parts.append(item)
                    elif images:
                        # Handle base64 images from numpy arrays
                        for i, image in enumerate(images):
                            if image is not None:
                                try:
                                    # Convert image to base64
                                    image_b64 = self._image_to_base64(image)
                                    content_parts.append({
                                        "type": "image",
                                        "url": f"data:image/png;base64,{image_b64}"
                                    })
                                    has_images = True
                                except Exception as e:
                                    print(f"Warning: Failed to process image {i}: {e}")
                        
                        # Add text content
                        if isinstance(msg['content'], str):
                            content_parts.append({"type": "text", "text": msg['content']})
                        elif isinstance(msg['content'], list):
                            for item in msg['content']:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    content_parts.append(item)
                                elif isinstance(item, str):
                                    content_parts.append({"type": "text", "text": item})
                    
                    if has_images:
                        # Stringify the content for Ollama API
                        content_string = json.dumps(content_parts)
                        
                        ollama_messages.append({
                            "role": msg['role'],
                            "content": content_string
                        })
                    else:
                        # Handle regular text content
                        if isinstance(msg['content'], list):
                            # Convert any arrays to strings
                            content_string = " ".join([str(item) for item in msg['content']])
                            ollama_messages.append({
                                "role": msg['role'],
                                "content": content_string
                            })
                        else:
                            ollama_messages.append(msg)
                else:
                    # Handle non-user messages
                    if isinstance(msg['content'], list):
                        # Convert any arrays to strings
                        content_string = " ".join([str(item) for item in msg['content']])
                        ollama_messages.append({
                            "role": msg['role'],
                            "content": content_string
                        })
                    else:
                        ollama_messages.append(msg)
            
            # Call Ollama API with increased timeout
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": ollama_messages,
                    "stream": False
                },
                timeout=120  # Increased timeout to 2 minutes
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result.get('message', {}).get('content', ''),
                    'mode': 'ollama',
                    'model': self.model_name
                }
            else:
                error_detail = response.text if response.text else f'Status: {response.status_code}'
                return {
                    'success': False,
                    'error': f'Ollama API error: {response.status_code} - {error_detail}',
                    'mode': 'ollama'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timed out. The model may still be loading. Please try again in a moment.',
                'mode': 'ollama'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'ollama'
            }
    
    def _chat_direct(self, messages: List[Dict], images: Optional[List[np.ndarray]] = None) -> Dict:
        """Chat using direct model loading"""
        try:
            if not self.direct_model or not self.direct_processor:
                raise Exception("Direct model not loaded")
            
            # Apply chat template
            input_ids = self.direct_processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            
            # Move to device
            input_ids = input_ids.to(self.direct_model.device, dtype=self.direct_model.dtype)
            
            # Generate response
            outputs = self.direct_model.generate(
                **input_ids, 
                max_new_tokens=128,
                do_sample=True,
                temperature=0.7
            )
            
            # Decode response
            response_text = self.direct_processor.batch_decode(
                outputs,
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False
            )[0]
            
            return {
                'success': True,
                'response': response_text,
                'mode': 'direct',
                'model': self.model_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'direct'
            }
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """Convert numpy image to base64 string"""
        # Convert to PIL Image
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        pil_image = Image.fromarray(image)
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    
    def get_status(self) -> Dict:
        """Get current model status"""
        status = {
            'mode': self.mode,
            'model_name': self.model_name,
            'direct_model_loaded': self.direct_model is not None,
            'ollama_url': self.ollama_url
        }
        
        if self.mode == "ollama":
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                status['ollama_connected'] = response.status_code == 200
            except:
                status['ollama_connected'] = False
        
        return status
    
    def switch_mode(self, new_mode: str):
        """Switch between direct and Ollama modes"""
        if new_mode == self.mode:
            return
        
        print(f"🔄 Switching from {self.mode} to {new_mode} mode...")
        
        if new_mode == "ollama":
            self.mode = "ollama"
            self._check_ollama_connection()
        elif new_mode == "direct":
            self.mode = "direct"
            self._load_direct_model()
        
        print(f"✅ Switched to {new_mode} mode")

# Global model manager instance
model_manager = None

def get_model_manager() -> ModelManager:
    """Get or create global model manager instance"""
    global model_manager
    if model_manager is None:
        model_manager = ModelManager()
    return model_manager 