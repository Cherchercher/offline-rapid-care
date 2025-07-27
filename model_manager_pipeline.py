import torch
from transformers import pipeline, AutoProcessor, AutoModelForImageTextToText
import requests
from PIL import Image
from io import BytesIO
import json
import io
import base64
from typing import Dict, List, Optional
import time
import os
from prompts import MEDICAL_TRIAGE_PROMPT

class ModelManagerPipeline:
    """Model manager using direct model loading for all tasks"""
    
    def __init__(self, model_path: str = "./models/gemma3n-local", device: str = None):
        """
        Initialize direct model manager
        
        Args:
            model_path: Path to local model or Hugging Face model name
            device: Device to run on ("cpu", "cuda:0", etc.) - auto-detects if None
        """
        self.model_path = model_path
        
        # Auto-detect device for Jetson
        if device is None:
            if torch.cuda.is_available():
                # Check if it's a Jetson device
                if os.path.exists("/etc/nv_tegra_release"):
                    print("🚀 Detected Jetson device, using CUDA")
                    self.device = "cuda:0"
                else:
                    print("🚀 Detected CUDA device, using GPU")
                    self.device = "cuda:0"
            else:
                print("🚀 No CUDA available, using CPU")
                self.device = "cpu"
        else:
            self.device = device
            
        print(f"🎯 Using device: {self.device}")
        
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
                device_map=self.device,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            self._model_loaded = True
            print("✅ Direct model loaded successfully")
            
        except Exception as e:
            print(f"❌ Failed to load direct model: {e}")
            raise
    
    def _load_image_from_url(self, url: str) -> Optional[Image.Image]:
        """Load image from URL or local path"""
        try:
            print(f"🔊 Loading image from URL/path: {url}")
            
            # Check if it's a local file path
            if os.path.exists(url):
                img = Image.open(url).convert("RGB")
                print(f"🔊 Successfully loaded local image: {img.size}")
                return img
            
            # Otherwise treat as URL
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGB")
            print(f"🔊 Successfully loaded image from URL: {img.size}")
            return img
        except Exception as e:
            print(f"🔊 Error loading image from URL/path {url}: {e}")
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
            
            # Apply chat template - let the processor handle images from messages
            print(f"🔊 Applying chat template with messages")
            template_start = time.time()
            input_ids = self.direct_processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            template_time = time.time() - template_start
            print(f"🔊 Chat template applied in {template_time:.2f} seconds")
            
            # Move to CPU with the same dtype as the model
            model_dtype = next(self.direct_model.parameters()).dtype
            input_ids = input_ids.to("cpu", dtype=model_dtype)
            print(f"🔊 Using model dtype: {model_dtype}")
            
            # --- ADDED: Input tensor validation ---
            for k, v in input_ids.items():
                if hasattr(v, 'shape'):
                    print(f"🔍 Tensor {k}: shape={v.shape}, dtype={v.dtype}, min={v.min().item()}, max={v.max().item()}, any NaN={torch.isnan(v).any().item()}, any Inf={torch.isinf(v).any().item()}")
                    if torch.isnan(v).any() or torch.isinf(v).any():
                        raise ValueError(f"Input tensor {k} contains NaN or Inf values!")
            # --- END ADDED ---
            
            # Generate response
            try:
                outputs = self.direct_model.generate(
                    **input_ids, 
                    max_new_tokens=256,
                    do_sample=True,
                    temperature=0.7
                )
            except RuntimeError as gen_err:
                print(f"❌ Model generate() failed: {gen_err}")
                # If probability tensor error, suggest updating model or preprocessing
                if 'probability tensor' in str(gen_err):
                    print("⚠️  Probability tensor error: consider updating model weights, preprocessing, or temperature parameter.")
                return {
                    'success': False,
                    'error': str(gen_err),
                    'mode': 'image-direct'
                }
            
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
        # Note: If probability tensor errors persist, consider updating model weights or preprocessing pipeline.
    
    def chat_video(self, messages: List[Dict]) -> Dict:
        """
        Send video analysis request using frame extraction and image analysis
        
        Args:
            messages: List of message dictionaries (video path should be embedded in messages)
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Extract video path from messages
            video_path = None
            for msg in messages:
                if isinstance(msg.get("content"), list):
                    for item in msg["content"]:
                        if isinstance(item, dict) and item.get("type") == "video":
                            video_path = item.get("path")
                            break
            
            if not video_path:
                return {
                    'success': False,
                    'error': 'No video path found in messages',
                    'mode': 'video-direct'
                }
            
            print(f"🔊 Video analysis request:")
            print(f"   Video path: {video_path}")
            
            # Check if video file exists
            if not os.path.exists(video_path):
                return {
                    'success': False,
                    'error': f'Video file not found: {video_path}',
                    'mode': 'video-direct'
                }
            
            start_time = time.time()
            
            # Extract frames from video
            frames = self._extract_video_frames(video_path)
            
            if not frames:
                return {
                    'success': False,
                    'error': 'No frames extracted from video',
                    'mode': 'video-direct'
                }
            
            print(f"🔊 Extracted {len(frames)} frames from video")
            
            # Create a single message with all frames
            print(f"🔊 Creating video analysis message with {len(frames)} frames")
            
            # Save frames and create content list
            content = []
            saved_frames = []
            
            print(f"🔊 Saving {len(frames)} frames...")
            save_start = time.time()
            
            for i, frame in enumerate(frames):
                # Save frame to uploads directory
                timestamp = int(time.time() * 1000)
                frame_filename = f"video_frame_{timestamp}_{i}.jpg"
                frame_path = os.path.join("uploads", frame_filename)
                frame.save(frame_path, format='JPEG')
                saved_frames.append(frame_path)
                
                # Add frame to content
                content.append({"type": "image", "url": frame_path})
            
            save_time = time.time() - save_start
            print(f"🔊 Frame saving completed in {save_time:.2f} seconds")
            
            # Add structured text prompt for medical triage assessment
            structured_prompt = MEDICAL_TRIAGE_PROMPT
            
            content.append({"type": "text", "text": structured_prompt})
            
            # Create single message with all frames
            video_messages = [
                {
                    "role": "user",
                    "content": content
                }
            ]
            
            # Use the same image analysis method (which now handles multiple images)
            print(f"🔊 Starting image analysis for {len(frames)} frames...")
            analysis_start = time.time()
            result = self.chat_image(video_messages)
            analysis_time = time.time() - analysis_start
            print(f"🔊 Image analysis completed in {analysis_time:.2f} seconds")
            
            # Clean up frame files
            for frame_path in saved_frames:
                try:
                    os.remove(frame_path)
                except:
                    pass
            
            end_time = time.time()
            inference_time = end_time - start_time
            
            print(f"🔊 Video analysis completed in {inference_time:.2f} seconds")
            
            # Add video-specific metadata to the result
            if result['success']:
                result['frames_analyzed'] = len(frames)
                result['total_frames'] = len(frames)
                result['mode'] = 'video-direct'
            
            return result
            
        except Exception as e:
            import traceback
            print(f"🔊 Video analysis error: {e}")
            print(f"🔊 Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e),
                'mode': 'video-direct'
            }
    
    def _extract_video_frames(self, video_path: str, max_frames: int = 3) -> List[Image.Image]:
        """
        Extract frames from video file
        
        Args:
            video_path: Path to video file
            max_frames: Maximum number of frames to extract
        
        Returns:
            List of PIL Images
        """
        try:
            import cv2
            
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print(f"❌ Could not open video file: {video_path}")
                return []
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            print(f"🔊 Video info: {total_frames} frames, {fps:.2f} fps, {duration:.2f}s duration")
            
            # Calculate frame intervals to extract
            if total_frames <= max_frames:
                frame_indices = list(range(total_frames))
            else:
                # Extract frames evenly distributed throughout the video
                step = total_frames // max_frames
                frame_indices = [i * step for i in range(max_frames)]
            
            frames = []
            for frame_idx in frame_indices:
                # Set frame position
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                
                # Read frame
                ret, frame = cap.read()
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame_rgb)
                    
                    frames.append(pil_image)
                    print(f"🔊 Extracted frame {frame_idx + 1}/{total_frames}")
                else:
                    print(f"⚠️  Failed to read frame {frame_idx}")
            
            # Release video capture
            cap.release()
            
            print(f"🔊 Successfully extracted {len(frames)} frames")
            return frames
            
        except ImportError:
            print("❌ OpenCV not available. Install with: pip install opencv-python")
            return []
        except Exception as e:
            print(f"❌ Error extracting video frames: {e}")
            return []
    
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