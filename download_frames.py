#!/usr/bin/env python3
"""
Download video frames from server for inspection
"""

import requests
import os
from datetime import datetime

def download_frames():
    """Download recent video frames from the server"""
    
    # Create local directory for frames
    local_dir = "downloaded_frames"
    os.makedirs(local_dir, exist_ok=True)
    
    # Get list of frame files from server
    try:
        # Try to get frame list from uploads directory
        response = requests.get("http://ec2-44-252-1-211.us-west-2.compute.amazonaws.com:11435/")
        print(f"Server response: {response.status_code}")
        
        # List common frame patterns
        frame_patterns = [
            "video_frame_*.jpg",
            "frame_*.jpg", 
            "*.jpg"
        ]
        
        print("🔍 Looking for frame files...")
        
        # Try to download recent frames
        timestamp = int(datetime.now().timestamp() * 1000)
        for i in range(10):  # Try last 10 possible frame numbers
            frame_name = f"video_frame_{timestamp - i}_{i}.jpg"
            frame_url = f"http://ec2-44-252-1-211.us-west-2.compute.amazonaws.com:11435/{frame_name}"
            
            try:
                response = requests.get(frame_url, timeout=5)
                if response.status_code == 200:
                    local_path = os.path.join(local_dir, frame_name)
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ Downloaded: {frame_name} ({len(response.content)} bytes)")
                else:
                    print(f"❌ Not found: {frame_name}")
            except Exception as e:
                print(f"❌ Error downloading {frame_name}: {e}")
        
        # Also try to download the original video
        video_url = "http://ec2-44-252-1-211.us-west-2.compute.amazonaws.com:11435/coming_out_of_fire.mp4"
        try:
            response = requests.get(video_url, timeout=30)
            if response.status_code == 200:
                local_video_path = os.path.join(local_dir, "coming_out_of_fire.mp4")
                with open(local_video_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Downloaded video: coming_out_of_fire.mp4 ({len(response.content)} bytes)")
            else:
                print(f"❌ Video not found: {video_url}")
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
    
    print(f"\n📁 Downloaded files saved to: {os.path.abspath(local_dir)}")
    print("🔍 You can now inspect the frames and video to see what's actually being analyzed")

if __name__ == "__main__":
    download_frames() 