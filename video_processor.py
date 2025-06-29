import cv2
import numpy as np
import base64
import io
from PIL import Image
import requests
import json
from datetime import datetime
import os
from typing import List, Dict, Optional, Tuple
from model_manager import get_model_manager

class VideoProcessor:
    """Video processing for medical triage using Gemma 3n"""
    
    def __init__(self, use_ollama: bool = True, ollama_url: str = "http://localhost:11434"):
        self.use_ollama = use_ollama
        self.ollama_url = ollama_url
        self.model_name = "gemma3n:e4b"
        
        # Get model manager
        self.model_manager = get_model_manager()
        
        # Video processing settings
        self.frame_interval = 2  # Process every 2nd frame
        self.max_frames = 10     # Maximum frames to process
        self.image_size = (512, 512)  # Resize images for model
        
        # Triage categories
        self.triage_levels = ["Red", "Yellow", "Green", "Black"]
        
    def extract_frames(self, video_path: str) -> List[np.ndarray]:
        """Extract key frames from video for analysis"""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        frame_count = 0
        processed_frames = 0
        
        while cap.isOpened() and processed_frames < self.max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % self.frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
                processed_frames += 1
                
            frame_count += 1
            
        cap.release()
        return frames
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for model input"""
        # Resize to model-compatible size
        resized = cv2.resize(frame, self.image_size)
        
        # Normalize pixel values
        normalized = resized.astype(np.float32) / 255.0
        
        return normalized
    
    def analyze_frame(self, frame: np.ndarray, role: str = "PARAMEDIC") -> Dict:
        """Analyze frame using the model manager"""
        try:
            # Preprocess frame
            processed_frame = self.preprocess_frame(frame)
            
            # Create system prompt for medical triage with specific output format
            system_prompt = f"""You are a {role.lower()} performing medical triage from video footage. 

CRITICAL OUTPUT FORMAT REQUIREMENTS:
You MUST respond in exactly this format:
**Triage: [RED/YELLOW/GREEN/BLACK]**
**Reasoning:** [2-3 sentences explaining triage decision]
**Action:** [3-5 specific, actionable steps]

TRIAGE CATEGORIES:
- RED: Life-threatening, immediate intervention needed
- YELLOW: Serious but stable, urgent care within 1 hour
- GREEN: Minor injuries, can wait for treatment
- BLACK: Deceased or injuries incompatible with life

ASSESSMENT FOCUS:
- Consciousness level (alert, responsive, unresponsive)
- Visible injuries and bleeding
- Breathing pattern and effort
- Age/gender indicators
- Overall scene safety

Keep reasoning concise and actions specific. Do not include any other text or formatting."""
            
            # Prepare messages for model
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Analyze this patient for medical triage assessment."}
            ]
            
            # Use model manager to get response
            result = self.model_manager.chat(messages, images=[processed_frame])
            
            if result['success']:
                description = result['response']
                triage_level = self.extract_triage_level(description)
                
                return {
                    'description': description,
                    'triage_level': triage_level,
                    'confidence': 0.8,
                    'timestamp': datetime.now().isoformat(),
                    'mode': result.get('mode', 'unknown')
                }
            else:
                return {
                    'error': result.get('error', 'Unknown error'),
                    'description': 'Analysis failed',
                    'triage_level': 'Unknown',
                    'mode': result.get('mode', 'unknown')
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'description': 'Analysis failed',
                'triage_level': 'Unknown'
            }
    
    def analyze_frame_with_ollama(self, frame: np.ndarray, role: str = "PARAMEDIC") -> Dict:
        """Legacy method - now uses model manager"""
        return self.analyze_frame(frame, role)
    
    def analyze_frame_direct(self, frame: np.ndarray, role: str = "PARAMEDIC") -> Dict:
        """Legacy method - now uses model manager"""
        return self.analyze_frame(frame, role)
    
    def analyze_frame_with_url(self, frame: np.ndarray, role: str = "PARAMEDIC", image_url: str = None) -> Dict:
        """Analyze frame using the model manager with image URL"""
        try:
            # Preprocess frame
            processed_frame = self.preprocess_frame(frame)
            
            # Create system prompt for medical triage with specific output format
            system_prompt = f"""You are a {role.lower()} performing medical triage from video footage. 

CRITICAL OUTPUT FORMAT REQUIREMENTS:
You MUST respond in exactly this format:
**Triage: [RED/YELLOW/GREEN/BLACK]**
**Reasoning:** [2-3 sentences explaining triage decision]
**Action:** [3-5 specific, actionable steps]

TRIAGE CATEGORIES:
- RED: Life-threatening, immediate intervention needed
- YELLOW: Serious but stable, urgent care within 1 hour
- GREEN: Minor injuries, can wait for treatment
- BLACK: Deceased or injuries incompatible with life

ASSESSMENT FOCUS:
- Consciousness level (alert, responsive, unresponsive)
- Visible injuries and bleeding
- Breathing pattern and effort
- Age/gender indicators
- Overall scene safety

Keep reasoning concise and actions specific. Do not include any other text or formatting."""
            
            # Prepare messages for model with image URL
            if image_url:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "image", "url": image_url},
                        {"type": "text", "text": "Analyze this patient for medical triage assessment."}
                    ]}
                ]
            else:
                # Fallback to base64 if no URL provided
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Analyze this patient for medical triage assessment."}
                ]
            
            # Use model manager to get response
            result = self.model_manager.chat(messages, images=[processed_frame] if not image_url else None)
            
            if result['success']:
                description = result['response']
                triage_level = self.extract_triage_level(description)
                
                return {
                    'description': description,
                    'triage_level': triage_level,
                    'confidence': 0.8,
                    'timestamp': datetime.now().isoformat(),
                    'mode': result.get('mode', 'unknown'),
                    'image_url': image_url
                }
            else:
                return {
                    'error': result.get('error', 'Unknown error'),
                    'description': 'Analysis failed',
                    'triage_level': 'Unknown',
                    'mode': result.get('mode', 'unknown')
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'description': 'Analysis failed',
                'triage_level': 'Unknown'
            }
    
    def classify_triage_level(self, description: str) -> str:
        """Classify triage level based on description"""
        description_lower = description.lower()
        
        # Red indicators
        red_keywords = ['unconscious', 'not breathing', 'cardiac arrest', 'severe bleeding', 'critical']
        if any(keyword in description_lower for keyword in red_keywords):
            return "Red"
        
        # Yellow indicators
        yellow_keywords = ['conscious', 'breathing', 'moderate', 'pain', 'injury']
        if any(keyword in description_lower for keyword in yellow_keywords):
            return "Yellow"
        
        # Black indicators
        black_keywords = ['deceased', 'dead', 'no pulse', 'rigor mortis']
        if any(keyword in description_lower for keyword in black_keywords):
            return "Black"
        
        # Default to Green
        return "Green"
    
    def extract_triage_level(self, description: str) -> str:
        """Extract triage level from model response"""
        description_lower = description.lower()
        
        # Look for triage indicators in the response
        if '**triage: red**' in description_lower or 'triage: red' in description_lower:
            return "Red"
        elif '**triage: yellow**' in description_lower or 'triage: yellow' in description_lower:
            return "Yellow"
        elif '**triage: black**' in description_lower or 'triage: black' in description_lower:
            return "Black"
        elif '**triage: green**' in description_lower or 'triage: green' in description_lower:
            return "Green"
        
        # Fallback to keyword-based classification
        return self.classify_triage_level(description)
    
    def process_video(self, video_path: str, role: str = "PARAMEDIC") -> Dict:
        """Process entire video and provide comprehensive analysis"""
        try:
            # Extract frames
            frames = self.extract_frames(video_path)
            
            if not frames:
                return {
                    'error': 'No frames extracted from video',
                    'analysis': []
                }
            
            # Analyze each frame
            analyses = []
            for i, frame in enumerate(frames):
                analysis = self.analyze_frame(frame, role)
                analysis['frame_number'] = i
                analyses.append(analysis)
            
            # Aggregate results
            triage_counts = {}
            for analysis in analyses:
                level = analysis.get('triage_level', 'Unknown')
                triage_counts[level] = triage_counts.get(level, 0) + 1
            
            # Determine overall triage level (highest priority wins)
            priority_order = ['Black', 'Red', 'Yellow', 'Green']
            overall_triage = 'Green'
            for level in priority_order:
                if triage_counts.get(level, 0) > 0:
                    overall_triage = level
                    break
            
            # Get most detailed description
            best_analysis = max(analyses, key=lambda x: len(x.get('description', '')))
            
            return {
                'video_path': video_path,
                'frames_analyzed': len(frames),
                'overall_triage': overall_triage,
                'triage_distribution': triage_counts,
                'primary_description': best_analysis.get('description', ''),
                'frame_analyses': analyses,
                'timestamp': datetime.now().isoformat(),
                'processing_method': self.model_manager.mode
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'video_path': video_path,
                'analysis': []
            }
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """Detect faces in frame for missing person identification"""
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Load face cascade classifier
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            face_data = []
            for (x, y, w, h) in faces:
                face_data.append({
                    'bbox': [x, y, w, h],
                    'center': [x + w//2, y + h//2],
                    'size': w * h
                })
            
            return face_data
            
        except Exception as e:
            return []
    
    def create_video_summary(self, analysis_results: Dict) -> str:
        """Create a human-readable summary of video analysis"""
        if 'error' in analysis_results:
            return f"Error processing video: {analysis_results['error']}"
        
        summary = f"""
Video Analysis Summary:
======================
Frames Analyzed: {analysis_results.get('frames_analyzed', 0)}
Overall Triage Level: {analysis_results.get('overall_triage', 'Unknown')}
Processing Method: {analysis_results.get('processing_method', 'Unknown')}

Triage Distribution:
"""
        
        for level, count in analysis_results.get('triage_distribution', {}).items():
            summary += f"- {level}: {count} frames\n"
        
        summary += f"\nPrimary Assessment: {analysis_results.get('primary_description', 'No description available')}"
        
        return summary
    
    def get_status(self) -> Dict:
        """Get video processor status"""
        return {
            'frame_interval': self.frame_interval,
            'max_frames': self.max_frames,
            'image_size': self.image_size,
            'model_status': self.model_manager.get_status(),
            'triage_levels': self.triage_levels
        }
    
    def parse_license_response(self, response_text: str) -> Dict:
        """Parse the structured license response into a dictionary"""
        patient_info = {}
        
        # Extract information using regex patterns
        import re
        
        # Name extraction - handle multiple possible formats
        name_match = re.search(r'\*\*Name:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if name_match:
            patient_info['name'] = name_match.group(1).strip()
        
        # Date of birth extraction - handle multiple possible formats
        dob_match = re.search(r'\*\*Date of Birth:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if not dob_match:
            dob_match = re.search(r'\*\*DOB:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if dob_match:
            patient_info['dob'] = dob_match.group(1).strip()
        
        # Address extraction
        address_match = re.search(r'\*\*Address:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if address_match:
            patient_info['address'] = address_match.group(1).strip()
        
        # License number extraction - handle multiple possible formats
        license_match = re.search(r'\*\*Driver\'s License Number:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if not license_match:
            license_match = re.search(r'\*\*License:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if license_match:
            patient_info['license_number'] = license_match.group(1).strip()
        
        # State extraction
        state_match = re.search(r'\*\*State:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if state_match:
            patient_info['state'] = state_match.group(1).strip()
        
        # Gender extraction
        gender_match = re.search(r'\*\*Gender:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if gender_match:
            patient_info['gender'] = gender_match.group(1).strip()
        
        # Expiration date extraction
        expires_match = re.search(r'\*\*Expires:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if expires_match:
            patient_info['expires'] = expires_match.group(1).strip()
        
        # Medical information extraction
        medical_match = re.search(r'\*\*Medical:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if medical_match:
            patient_info['medical_info'] = medical_match.group(1).strip()
        
        # Notes extraction
        notes_match = re.search(r'\*\*Notes:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if notes_match:
            patient_info['notes'] = notes_match.group(1).strip()
        
        # PDF417 Data extraction
        pdf417_match = re.search(r'\*\*PDF417 Data:\*\*\s*(.+?)(?=\*\*|$)', response_text, re.IGNORECASE | re.DOTALL)
        if pdf417_match:
            patient_info['pdf417_data'] = pdf417_match.group(1).strip()
        
        # Calculate age from DOB if available
        if patient_info.get('dob'):
            try:
                from datetime import datetime
                # Try different date formats
                dob_str = patient_info['dob']
                dob_date = None
                
                # Try MM/DD/YYYY format first
                try:
                    dob_date = datetime.strptime(dob_str, '%m/%d/%Y')
                except:
                    # Try other common formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y']:
                        try:
                            dob_date = datetime.strptime(dob_str, fmt)
                            break
                        except:
                            continue
                
                if dob_date:
                    age = datetime.now().year - dob_date.year
                    if datetime.now().month < dob_date.month or (datetime.now().month == dob_date.month and datetime.now().day < dob_date.day):
                        age -= 1
                    patient_info['age'] = str(age)
                else:
                    patient_info['age'] = 'Unknown'
            except:
                patient_info['age'] = 'Unknown'
        
        return patient_info

# Example usage and testing
if __name__ == "__main__":
    # Test the video processor
    processor = VideoProcessor()
    
    # Print status
    print("Video Processor Status:")
    print(json.dumps(processor.get_status(), indent=2))
    
    # Test with a sample video (if available)
    test_video = "sample_casualty.mp4"
    
    if os.path.exists(test_video):
        print("\nProcessing test video...")
        results = processor.process_video(test_video, "PARAMEDIC")
        print(processor.create_video_summary(results))
    else:
        print("\nNo test video found. Create a sample video to test the processor.")
        print("You can create a test video or use an existing video file.") 