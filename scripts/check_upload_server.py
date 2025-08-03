#!/usr/bin/env python3
"""
Check upload server status and file access
"""
import requests
import os
import time

def check_upload_server():
    print("🔍 Checking Upload Server...")
    
    # Check if upload server is running
    try:
        response = requests.get('http://localhost:11435', timeout=5)
        print(f"✅ Upload server is running: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Upload server not accessible: {e}")
    
    # Check if we can access the uploads directory
    print(f"\n📁 Checking uploads directory...")
    if os.path.exists('uploads'):
        files = os.listdir('uploads')
        print(f"✅ Uploads directory exists with {len(files)} files:")
        for file in files[:10]:  # Show first 10 files
            file_path = os.path.join('uploads', file)
            size = os.path.getsize(file_path)
            print(f"   {file} ({size} bytes)")
    else:
        print("❌ Uploads directory doesn't exist")
    
    # Check /tmp directory
    print(f"\n📁 Checking /tmp directory...")
    if os.path.exists('/tmp'):
        tmp_files = [f for f in os.listdir('/tmp') if f.startswith('tmp') and f.endswith('.mp4')]
        print(f"✅ /tmp directory exists with {len(tmp_files)} temp video files:")
        for file in tmp_files:
            file_path = os.path.join('/tmp', file)
            size = os.path.getsize(file_path)
            print(f"   {file} ({size} bytes)")
    else:
        print("❌ /tmp directory doesn't exist")

if __name__ == "__main__":
    check_upload_server() 