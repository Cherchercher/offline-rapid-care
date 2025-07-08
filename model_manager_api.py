import requests
import json
from typing import Dict, List, Optional
import time

class ModelManagerAPI:
    """Model manager that communicates with the model API server"""
    
    def __init__(self, api_url: str = "http://localhost:5001"):
        """
        Initialize API-based model manager
        
        Args:
            api_url: URL of the model API server
        """
        self.api_url = api_url
        self.health_url = f"{api_url}/health"
        self.chat_text_url = f"{api_url}/chat/text"
        self.chat_image_url = f"{api_url}/chat/image"
        self.chat_video_url = f"{api_url}/chat/video"
        self.chat_audio_url = f"{api_url}/chat/audio"
        self.status_url = f"{api_url}/status"
        
    def _check_server_health(self) -> bool:
        """Check if the model server is healthy"""
        try:
            response = requests.get(self.health_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def chat_text(self, messages: List[Dict]) -> Dict:
        """
        Send text-only chat request to model API server
        
        Args:
            messages: List of message dictionaries
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            print(f"🔗 API Model Manager: Attempting to connect to {self.api_url}")
            
            # Check server health first
            if not self._check_server_health():
                print(f"❌ API Model Manager: Server health check failed")
                return {
                    'success': False,
                    'error': 'Model API server is not available',
                    'mode': 'api'
                }
            
            print(f"✅ API Model Manager: Server health check passed")
            
            # Prepare request payload
            payload = {
                'messages': messages
            }
            
            # Send request to text endpoint
            response = requests.post(
                self.chat_text_url,
                json=payload,
                timeout=300  # 5 minutes timeout for model inference
            )
            
            if response.status_code == 200:
                result = response.json()
                result['mode'] = 'api-text'
                return result
            else:
                return {
                    'success': False,
                    'error': f'API server error: {response.status_code}',
                    'mode': 'api-text'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout - model inference took too long',
                'mode': 'api-text'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'api-text'
            }
    
    def chat_image(self, messages: List[Dict]) -> Dict:
        """
        Send image analysis request to model API server
        
        Args:
            messages: List of message dictionaries (images should be embedded in messages)
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            print(f"🔗 API Model Manager: Attempting to connect to {self.api_url}")
            
            # Check server health first
            if not self._check_server_health():
                print(f"❌ API Model Manager: Server health check failed")
                return {
                    'success': False,
                    'error': 'Model API server is not available',
                    'mode': 'api'
                }
            
            print(f"✅ API Model Manager: Server health check passed")
            
            # Prepare request payload
            payload = {
                'messages': messages
            }
            
            # Send request to image endpoint
            response = requests.post(
                self.chat_image_url,
                json=payload,
                timeout=300  # 5 minutes timeout for model inference
            )
            
            if response.status_code == 200:
                result = response.json()
                result['mode'] = 'api-image'
                return result
            else:
                return {
                    'success': False,
                    'error': f'API server error: {response.status_code}',
                    'mode': 'api-image'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout - model inference took too long',
                'mode': 'api-image'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'api-image'
            }
    
    def chat_audio(self, messages: List[Dict]) -> Dict:
        """
        Send audio transcription request to model API server
        
        Args:
            messages: List of message dictionaries (audio path should be embedded in messages)
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            print(f"🔗 API Model Manager: Attempting to connect to {self.api_url}")
            
            # Check server health first
            if not self._check_server_health():
                print(f"❌ API Model Manager: Server health check failed")
                return {
                    'success': False,
                    'error': 'Model API server is not available',
                    'mode': 'api'
                }
            
            print(f"✅ API Model Manager: Server health check passed")
            
            # Prepare request payload
            payload = {
                'messages': messages
            }
            
            # Send request to audio endpoint
            response = requests.post(
                self.chat_audio_url,
                json=payload,
                timeout=600  # 10 minutes for audio transcription
            )
            
            if response.status_code == 200:
                result = response.json()
                result['mode'] = 'api-audio'
                return result
            else:
                return {
                    'success': False,
                    'error': f'API server error: {response.status_code}',
                    'mode': 'api-audio'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout - audio transcription took too long',
                'mode': 'api-audio'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'api-audio'
            }
    
    def chat_video(self, messages: List[Dict]) -> Dict:
        """
        Send video analysis request to model API server
        
        Args:
            messages: List of message dictionaries (video path should be embedded in messages)
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            print(f"🔗 API Model Manager: Attempting to connect to {self.api_url}")
            
            # Check server health first
            if not self._check_server_health():
                print(f"❌ API Model Manager: Server health check failed")
                return {
                    'success': False,
                    'error': 'Model API server is not available',
                    'mode': 'api'
                }
            
            print(f"✅ API Model Manager: Server health check passed")
            
            # Prepare request payload
            payload = {
                'messages': messages
            }
            
            # Send request to video endpoint
            response = requests.post(
                f"{self.api_url}/chat/video",
                json=payload,
                timeout=300  # 5 minutes for video processing (frame extraction + analysis)
            )
            
            if response.status_code == 200:
                result = response.json()
                result['mode'] = 'api-video'
                return result
            else:
                return {
                    'success': False,
                    'error': f'API server error: {response.status_code}',
                    'mode': 'api-video'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout - video analysis took too long',
                'mode': 'api-video'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'api-video'
            }
    
    def transcribe_audio_file(self, audio_file_path: str, prompt: str = "Transcribe this audio accurately") -> Dict:
        """
        Transcribe audio file using the new API architecture
        
        Args:
            audio_file_path: Path to audio file
            prompt: Transcription prompt
        
        Returns:
            Dictionary with transcription result
        """
        try:
            # Create messages with audio path
            messages = [
                {"role": "user", "content": [
                    {"type": "audio", "audio": audio_file_path},
                    {"type": "text", "text": prompt}
                ]}
            ]
            
            # Use the audio endpoint
            return self.chat_audio(messages)
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'api-audio'
            }
    
    def chat(self, messages: List[Dict], images: Optional[List] = None) -> Dict:
        """
        Legacy method - redirects to appropriate endpoint based on content
        """
        if images or any('image' in str(msg) for msg in messages):
            return self.chat_image(messages, images)
        elif any('audio' in str(msg) for msg in messages):
            return self.chat_audio(messages)
        else:
            return self.chat_text(messages)
    
    def get_status(self) -> Dict:
        """Get current model status from API server"""
        try:
            response = requests.get(self.status_url, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'mode': 'api',
                    'error': f'Status check failed: {response.status_code}'
                }
        except:
            return {
                'mode': 'api',
                'error': 'Cannot connect to model API server'
            }

def get_api_model_manager() -> ModelManagerAPI:
    """Get API-based model manager instance"""
    return ModelManagerAPI() 