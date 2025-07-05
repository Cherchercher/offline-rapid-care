#!/usr/bin/env python3
"""
Convert audio files to WAV format for better compatibility
"""

import os
import subprocess
import tempfile
from pathlib import Path

def convert_to_wav(input_path, output_path=None):
    """
    Convert audio file to WAV format using ffmpeg
    
    Args:
        input_path: Path to input audio file
        output_path: Path for output WAV file (optional)
    
    Returns:
        Path to the converted WAV file
    """
    try:
        if output_path is None:
            # Create output path with .wav extension
            input_path = Path(input_path)
            output_path = input_path.parent / f"{input_path.stem}_converted.wav"
        
        # Use ffmpeg to convert to WAV
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',          # 16kHz sample rate
            '-ac', '1',              # Mono
            '-y',                    # Overwrite output file
            str(output_path)
        ]
        
        print(f"🔊 Converting {input_path} to WAV...")
        print(f"   Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Converted to: {output_path}")
            return str(output_path)
        else:
            print(f"❌ Conversion failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error converting audio: {e}")
        return None

def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

if __name__ == "__main__":
    # Test conversion
    if not check_ffmpeg():
        print("❌ ffmpeg not found. Please install it first:")
        print("   sudo yum install ffmpeg")
    else:
        print("✅ ffmpeg is available") 