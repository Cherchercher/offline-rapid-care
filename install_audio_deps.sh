#!/bin/bash
# Install audio processing dependencies

echo "Installing audio processing dependencies..."

# Install system audio libraries
sudo yum install -y ffmpeg ffmpeg-devel

# Install Python audio processing libraries
pip3 install pydub
pip3 install librosa
pip3 install soundfile

echo "Audio dependencies installed!"
echo "Supported formats: MP3, WAV, M4A, OGG, FLAC" 