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
import cv2
from prompts import MEDICAL_TRIAGE_PROMPT

# Try to import Unsloth for FastVisionModel
try:
    from unsloth import FastVisionModel
    UNSLOTH_AVAILABLE = True
    print("✅ Unsloth FastVisionModel available")
except ImportError:
    UNSLOTH_AVAILABLE = False
    print("⚠️  Unsloth not available, using standard model loading")

class ModelManagerPipeline:
    """Model manager using direct model loading for all tasks"""
    
    def __init__(self, model_path: str = "./models/gemma3n-4b", device: str = None):
        """
        Initialize direct model manager
        
        Args:
            model_path: Path to local model or Hugging Face model name
            device: Device to run on ("cpu", "cuda:0", etc.) - auto-detects if None
        """
        self.model_path = model_path
        
        # Auto-detect device for any GPU
        if device is None:
            if torch.cuda.is_available():
                # Check if it's a Jetson device (multiple indicators)
                is_jetson = self._is_jetson_device()
                if is_jetson:
                    print("🚀 Detected Jetson device, using CUDA")
                else:
                    print("🚀 Detected standard GPU device, using CUDA")
                self.device = "cuda:0"
            else:
                print("🚀 No CUDA available, using CPU")
                self.device = "cpu"
        else:
            self.device = device
            
        print(f"🎯 Using device: {self.device}")
        
        # Print device capabilities
        if self.device == "cuda:0" and torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            device_type = "Jetson" if self._is_jetson_device() else "Standard GPU"
            print(f"📊 GPU: {gpu_name} ({gpu_memory:.1f} GB) - {device_type}")
        
        self.direct_model = None
        self.direct_processor = None
        self._model_loaded = False
        
        # GPU memory optimization for all CUDA devices
        if self.device == "cuda:0" and torch.cuda.is_available():
            print("🚀 Setting up GPU optimizations...")
            
            # Check if it's Jetson
            is_jetson = self._is_jetson_device()
            if is_jetson:
                print("   🎯 Jetson device detected - using specialized optimizations")
                # Jetson-specific memory fraction (more conservative)
                torch.cuda.set_per_process_memory_fraction(0.8)
            else:
                print("   🎯 Standard GPU device detected")
                # Standard GPU memory fraction
                torch.cuda.set_per_process_memory_fraction(0.9)
            
            # Enable memory efficient attention if available
            try:
                torch.backends.cuda.enable_flash_sdp(True)
                print("   ✅ Flash attention enabled")
            except:
                print("   ⚠️  Flash attention not available")
            
            # Clear GPU cache
            torch.cuda.empty_cache()
            print("   ✅ GPU memory cache cleared")
            
            # Print GPU info
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"   📊 GPU: {gpu_name} ({gpu_memory:.1f} GB)")
            print(f"   🎯 Device type: {'Jetson' if is_jetson else 'Standard GPU'}")
        
    def _load_direct_model(self):
        """Load model directly using transformers (lazily on first use)"""
        if self._model_loaded:
            return
            
        print("🔄 Loading Gemma 3n model directly...")
        
        try:
            # Use local model path
            local_model_path = self.model_path
            
            # Check if local model exists
            if not os.path.exists(local_model_path):
                print(f"❌ Local model not found at {local_model_path}")
                raise FileNotFoundError(f"Local model not found at {local_model_path}")
            
            # Load processor and model from local directory
            self.direct_processor = AutoProcessor.from_pretrained(
                local_model_path, 
                trust_remote_code=True
            )
            
            # Load model with GPU optimizations
            if self.device == "cuda:0" and torch.cuda.is_available():
                is_jetson = self._is_jetson_device()
                
                if is_jetson:
                    print("🚀 Loading model with Jetson optimizations...")
                    # Use float16 for Jetson GPU memory efficiency
                    self.direct_model = AutoModelForImageTextToText.from_pretrained(
                        local_model_path, 
                        torch_dtype=torch.float16, 
                        device_map=self.device,
                        trust_remote_code=True,
                        low_cpu_mem_usage=True
                    )
                    print("✅ Model loaded with float16 on Jetson GPU")
                else:
                    print("🚀 Loading model with standard GPU optimizations...")
                    # Use auto dtype for standard GPUs (can handle higher precision)
                    self.direct_model = AutoModelForImageTextToText.from_pretrained(
                        local_model_path, 
                        torch_dtype="auto", 
                        device_map=self.device,
                        trust_remote_code=True,
                        low_cpu_mem_usage=True
                    )
                    print("✅ Model loaded with auto dtype on standard GPU")
            else:
                # CPU loading
                print("🚀 Loading model on CPU...")
                self.direct_model = AutoModelForImageTextToText.from_pretrained(
                    local_model_path, 
                    torch_dtype="auto", 
                    device_map=self.device,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
                print("✅ Model loaded on CPU")
            
            # Try to enable Unsloth FastVisionModel.for_inference() if available
            try:
                if UNSLOTH_AVAILABLE and hasattr(self.direct_model, 'for_inference'):
                    self.direct_model = self.direct_model.for_inference()
                    print("✅ Unsloth FastVisionModel.for_inference() enabled")
                elif UNSLOTH_AVAILABLE:
                    print("⚠️  FastVisionModel.for_inference() not available on this model")
                else:
                    print("⚠️  Unsloth not available, using standard model loading")
            except Exception as e:
                print(f"⚠️  Could not enable FastVisionModel.for_inference(): {e}")
            
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
            
            # Move to the same device as the model
            model_dtype = next(self.direct_model.parameters()).dtype
            input_ids = input_ids.to(self.device, dtype=model_dtype)
            print(f"🔊 Using model dtype: {model_dtype} on device: {self.device}")
            
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
                'model': 'gemma3n-4b',
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
            
            # Extract image and text from messages (compatible with Colab approach)
            image = None
            prompt_text = ""
            
            for msg in messages:
                if isinstance(msg.get("content"), list):
                    for item in msg["content"]:
                        if isinstance(item, dict):
                            if item.get("type") == "image" and "image" in item:
                                image = item["image"]
                            elif item.get("type") == "text":
                                prompt_text = item.get("text", "")
            
            if image is None:
                return {
                    'success': False,
                    'error': 'No image found in messages',
                    'mode': 'image-direct'
                }
            
            # Use Colab-compatible approach
            print(f"🔊 Processing image with Colab-compatible method")
            
            # Create messages in Colab format
            colab_messages = [
                {
                    "role": "user",
                    "content": [{"type": "image"}, {"type": "text", "text": prompt_text}],
                }
            ]
            
            # Apply chat template like Colab
            input_text = self.direct_processor.apply_chat_template(
                colab_messages, 
                add_generation_prompt=True
            )
            
            # Process inputs like Colab
            inputs = self.direct_processor(
                image,
                input_text,
                add_special_tokens=False,
                return_tensors="pt"
            ).to(self.device)
            
            print(f"🔊 Inputs processed, shape: {inputs['input_ids'].shape}")
            
            # Generate with Colab parameters
            outputs = self.direct_model.generate(
                **inputs,
                max_new_tokens=512,  # Increased for better responses
                temperature=1.0,
                top_p=0.95,
                top_k=64,
                use_cache=True
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
            
            # Extract just the model's response
            if '<start_of_turn>model' in response_text:
                model_response = response_text.split('<start_of_turn>model')[-1]
                if '<end_of_turn>' in model_response:
                    model_response = model_response.split('<end_of_turn>')[0]
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
                'model': 'gemma3n-4b',
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
            print(f"🎬 === MODEL MANAGER PIPELINE VIDEO START ===")
            print(f"   Messages received: {json.dumps(messages, indent=2)}")
            
            # Extract video path from messages
            video_path = None
            for msg in messages:
                if isinstance(msg.get("content"), list):
                    for item in msg["content"]:
                        if isinstance(item, dict) and item.get("type") == "video":
                            video_path = item.get("path")
                            break
            
            if not video_path:
                print(f"❌ No video path found in messages")
                return {
                    'success': False,
                    'error': 'No video path found in messages',
                    'mode': 'video-direct'
                }
            
            print(f"🔊 Video analysis request:")
            print(f"   Video path: {video_path}")
            
            # Check if video file exists
            print(f"🔍 Checking if video file exists: {video_path}")
            file_exists = os.path.exists(video_path)
            print(f"   File exists: {file_exists}")
            
            if not file_exists:
                print(f"❌ Video file not found: {video_path}")
                # List contents of the directory
                dir_path = os.path.dirname(video_path)
                if os.path.exists(dir_path):
                    print(f"   Directory contents: {os.listdir(dir_path)}")
                else:
                    print(f"   Directory does not exist: {dir_path}")
                
                return {
                    'success': False,
                    'error': f'Video file not found: {video_path}',
                    'mode': 'video-direct'
                }
            
            start_time = time.time()
            
            # Extract frames from video
            frames = self._extract_video_frames(video_path)
            
            if not frames:
                print(f"❌ No frames extracted from video: {video_path}")
                # Try to get more info about the video file

                if os.path.exists(video_path):
                    print(f"   File size: {os.path.getsize(video_path)} bytes")
                    # Try to check if it's a valid video file
                    import subprocess
                    try:
                        result = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path], capture_output=True, text=True)
                        if result.returncode == 0:
                            print(f"   Video file is valid according to ffprobe")
                        else:
                            print(f"   Video file may be corrupted or unsupported format")
                    except:
                        print(f"   Could not check video format with ffprobe")
                else:
                    print(f"   Video file does not exist")
                
                return {
                    'success': False,
                    'error': 'No frames extracted from video. Please ensure the video file is valid and in a supported format (MP4, AVI, MOV).',
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
            
            print(f"🔊 Starting video frame extraction:")
            print(f"   Video path: {video_path}")
            print(f"   File exists: {os.path.exists(video_path)}")
            print(f"   File size: {os.path.getsize(video_path) if os.path.exists(video_path) else 'N/A'} bytes")
            
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print(f"❌ Could not open video file: {video_path}")
                print(f"   Trying to check video format...")
                # Try to get more info about the file
                import subprocess
                try:
                    result = subprocess.run(['file', video_path], capture_output=True, text=True)
                    print(f"   File type: {result.stdout.strip()}")
                except:
                    print(f"   Could not determine file type")
                return []
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"🔊 Video info: {total_frames} frames, {fps:.2f} fps, {duration:.2f}s duration, {width}x{height}")
            
            if total_frames <= 0:
                print(f"❌ Invalid video: {total_frames} frames")
                cap.release()
                return []
            
            # Calculate frame intervals to extract
            if total_frames <= max_frames:
                frame_indices = list(range(total_frames))
            else:
                # Extract frames evenly distributed throughout the video
                step = total_frames // max_frames
                frame_indices = [i * step for i in range(max_frames)]
            
            print(f"🔊 Will extract frames at indices: {frame_indices}")
            
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
            import traceback
            print(f"❌ Error extracting video frames: {e}")
            print(f"❌ Full traceback: {traceback.format_exc()}")
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
            
            # Move to the same device as the model
            model_dtype = next(self.direct_model.parameters()).dtype
            input_ids = input_ids.to(self.device, dtype=model_dtype)
            print(f"🔊 Using model dtype: {model_dtype} on device: {self.device}")
            
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
        status = {
            'mode': 'direct',
            'model_path': self.model_path,
            'device': self.device,
            'model_loaded': self._model_loaded,
            'direct_model_loaded': self.direct_model is not None,
            'direct_processor_loaded': self.direct_processor is not None
        }
        
        # Add GPU info if available
        if torch.cuda.is_available():
            status['gpu_name'] = torch.cuda.get_device_name(0)
            status['gpu_memory_total'] = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
            status['gpu_memory_allocated'] = torch.cuda.memory_allocated(0) / 1024**3  # GB
            status['gpu_memory_cached'] = torch.cuda.memory_reserved(0) / 1024**3  # GB
            status['is_jetson'] = os.path.exists("/etc/nv_tegra_release")
        
        return status

    def _is_jetson_device(self) -> bool:
        """Robust Jetson device detection (multiple indicators)"""
        try:
            jetson_indicators = [
                "/etc/nv_tegra_release",
                "/proc/device-tree/model",
                "/sys/module/tegra_fuse/parameters/tegra_chip_id"
            ]
            for indicator in jetson_indicators:
                if os.path.exists(indicator):
                    return True
            # Check GPU name for Jetson/Tegra/Xavier
            if torch.cuda.is_available():
                try:
                    device_name = torch.cuda.get_device_name(0).lower()
                    if any(x in device_name for x in ["tegra", "jetson", "xavier"]):
                        return True
                except Exception:
                    pass
            return False
        except Exception:
            return False

# Global instance
_pipeline_manager = None

def get_pipeline_manager() -> ModelManagerPipeline:
    """Get global pipeline manager instance"""
    global _pipeline_manager
    if _pipeline_manager is None:
        _pipeline_manager = ModelManagerPipeline()
    return _pipeline_manager 
