#!/usr/bin/env python3
"""
Compare Jetson detection between host and Docker container
"""

import requests
import json
import subprocess
import sys

def check_host_environment():
    """Check Jetson detection on host system"""
    print("🏠 HOST SYSTEM CHECK")
    print("=" * 50)
    
    try:
        # Import and test offline storage on host
        from offline_storage_manager import offline_storage
        
        is_jetson = offline_storage.is_jetson_device()
        capabilities = offline_storage.get_device_capabilities()
        
        print(f"   Is Jetson: {is_jetson}")
        print(f"   Has CUDA: {capabilities.get('has_cuda')}")
        print(f"   Device Count: {capabilities.get('device_count')}")
        print(f"   Memory Available: {capabilities.get('memory_available')} GB")
        print(f"   Offline Processing Supported: {capabilities.get('offline_processing_supported')}")
        
        return capabilities
        
    except Exception as e:
        print(f"   ❌ Error on host: {e}")
        return None

def check_container_environment():
    """Check Jetson detection inside Docker container"""
    print("\n🐳 DOCKER CONTAINER CHECK")
    print("=" * 50)
    
    try:
        # Check if container is running
        result = subprocess.run(['sudo', 'docker', 'ps'], capture_output=True, text=True)
        if 'offline-gemma-jetson' not in result.stdout:
            print("   ❌ Container not running")
            return None
        
        # Test Jetson detection inside container
        print("   Testing Jetson detection inside container...")
        
        # Check Jetson files in container
        jetson_files = [
            "/etc/nv_tegra_release",
            "/proc/device-tree/model"
        ]
        
        for file_path in jetson_files:
            result = subprocess.run(['sudo', 'docker', 'exec', 'offline-gemma-jetson', 'test', '-f', file_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {file_path} - EXISTS in container")
            else:
                print(f"   ❌ {file_path} - NOT FOUND in container")
        
        # Test CUDA in container
        result = subprocess.run(['sudo', 'docker', 'exec', 'offline-gemma-jetson', 'python3', '-c', 
                               'import torch; print("CUDA:", torch.cuda.is_available()); print("Device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   CUDA Test: {result.stdout.strip()}")
        else:
            print(f"   ❌ CUDA Test failed: {result.stderr.strip()}")
        
        # Test the actual API endpoint
        print("\n   Testing API endpoint...")
        response = requests.get("http://localhost:5050/api/device/capabilities", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            capabilities = data.get('capabilities', {})
            
            print(f"   API Response - Is Jetson: {capabilities.get('is_jetson')}")
            print(f"   API Response - Has CUDA: {capabilities.get('has_cuda')}")
            print(f"   API Response - Device Count: {capabilities.get('device_count')}")
            print(f"   API Response - Offline Processing: {capabilities.get('offline_processing_supported')}")
            
            return capabilities
        else:
            print(f"   ❌ API returned status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error checking container: {e}")
        return None

def compare_results(host_capabilities, container_capabilities):
    """Compare host vs container results"""
    print("\n📊 COMPARISON")
    print("=" * 50)
    
    if host_capabilities and container_capabilities:
        print("   Host vs Container:")
        print(f"     Is Jetson: {host_capabilities.get('is_jetson')} vs {container_capabilities.get('is_jetson')}")
        print(f"     Has CUDA: {host_capabilities.get('has_cuda')} vs {container_capabilities.get('has_cuda')}")
        print(f"     Device Count: {host_capabilities.get('device_count')} vs {container_capabilities.get('device_count')}")
        print(f"     Offline Processing: {host_capabilities.get('offline_processing_supported')} vs {container_capabilities.get('offline_processing_supported')}")
        
        # Check for mismatches
        mismatches = []
        for key in ['is_jetson', 'has_cuda', 'device_count', 'offline_processing_supported']:
            if host_capabilities.get(key) != container_capabilities.get(key):
                mismatches.append(key)
        
        if mismatches:
            print(f"\n   ❌ MISMATCHES FOUND: {mismatches}")
            print("   This explains why the API shows different results!")
        else:
            print(f"\n   ✅ NO MISMATCHES - Both environments agree")
            
    else:
        print("   ❌ Cannot compare - missing data from one environment")

def main():
    """Run the comparison"""
    print("🔍 Host vs Container Jetson Detection Comparison")
    print("=" * 60)
    
    host_capabilities = check_host_environment()
    container_capabilities = check_container_environment()
    
    compare_results(host_capabilities, container_capabilities)
    
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    
    if host_capabilities and container_capabilities:
        if host_capabilities.get('is_jetson') != container_capabilities.get('is_jetson'):
            print("   🔧 SOLUTION: The container needs access to Jetson files")
            print("   Try: sudo docker run --privileged ... or mount /etc/nv_tegra_release")
        elif host_capabilities.get('has_cuda') != container_capabilities.get('has_cuda'):
            print("   🔧 SOLUTION: The container needs CUDA access")
            print("   Make sure --gpus all is used when running the container")
        else:
            print("   ✅ Both environments are consistent")

if __name__ == "__main__":
    main() 