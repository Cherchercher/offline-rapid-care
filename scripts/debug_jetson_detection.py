#!/usr/bin/env python3
"""
Debug Jetson detection issues
"""

import os
import subprocess
import sys

def check_jetson_indicators():
    """Check all Jetson-specific indicators"""
    print("🔍 Checking Jetson Detection Indicators")
    print("=" * 50)
    
    # Check Jetson-specific files
    jetson_files = [
        "/etc/nv_tegra_release",
        "/proc/device-tree/model", 
        "/sys/module/tegra_fuse/parameters/tegra_chip_id"
    ]
    
    print("\n📁 Jetson-specific files:")
    for file_path in jetson_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path} - EXISTS")
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    print(f"      Content: {content}")
            except Exception as e:
                print(f"      Error reading: {e}")
        else:
            print(f"   ❌ {file_path} - NOT FOUND")
    
    # Check CUDA availability
    print("\n🎮 CUDA Detection:")
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"   CUDA Available: {cuda_available}")
        
        if cuda_available:
            device_count = torch.cuda.device_count()
            print(f"   Device Count: {device_count}")
            
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                print(f"   Device {i}: {device_name}")
                
                # Check for Jetson keywords in device name
                device_lower = device_name.lower()
                if 'tegra' in device_lower or 'jetson' in device_lower:
                    print(f"      ✅ Jetson keywords found in device name")
                else:
                    print(f"      ❌ No Jetson keywords in device name")
        else:
            print("   ❌ No CUDA devices available")
            
    except Exception as e:
        print(f"   ❌ Error checking CUDA: {e}")
    
    # Check system information
    print("\n💻 System Information:")
    try:
        # Check uname
        result = subprocess.run(['uname', '-a'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   System: {result.stdout.strip()}")
        
        # Check CPU info
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                cpu_info = f.read()
                if 'ARM' in cpu_info:
                    print("   ✅ ARM processor detected")
                else:
                    print("   ❌ Not ARM processor")
                    
    except Exception as e:
        print(f"   ❌ Error getting system info: {e}")
    
    # Check environment variables
    print("\n🌍 Environment Variables:")
    jetson_env_vars = [
        'JETSON_MODEL',
        'JETSON_VERSION', 
        'TEGRA_CHIP_ID',
        'CUDA_VISIBLE_DEVICES'
    ]
    
    for var in jetson_env_vars:
        value = os.environ.get(var)
        if value:
            print(f"   {var}: {value}")
        else:
            print(f"   {var}: Not set")

def test_offline_storage_detection():
    """Test the offline storage manager's Jetson detection"""
    print("\n🧪 Testing Offline Storage Manager Detection")
    print("=" * 50)
    
    try:
        from offline_storage_manager import offline_storage
        
        # Test Jetson detection
        is_jetson = offline_storage.is_jetson_device()
        print(f"   Offline Storage Manager - Is Jetson: {is_jetson}")
        
        # Test device capabilities
        capabilities = offline_storage.get_device_capabilities()
        print(f"   Device Capabilities:")
        for key, value in capabilities.items():
            print(f"     {key}: {value}")
            
    except Exception as e:
        print(f"   ❌ Error testing offline storage: {e}")

def check_docker_environment():
    """Check if running in Docker and how it affects detection"""
    print("\n🐳 Docker Environment Check")
    print("=" * 50)
    
    # Check if running in container
    if os.path.exists('/.dockerenv'):
        print("   ✅ Running in Docker container")
    else:
        print("   ❌ Not running in Docker container")
    
    # Check if Jetson files are accessible in container
    jetson_files = [
        "/etc/nv_tegra_release",
        "/proc/device-tree/model"
    ]
    
    print("   Jetson files in container:")
    for file_path in jetson_files:
        if os.path.exists(file_path):
            print(f"     ✅ {file_path} - EXISTS")
        else:
            print(f"     ❌ {file_path} - NOT FOUND")
    
    # Check if CUDA is available in container
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"   CUDA in container: {cuda_available}")
        
        if cuda_available:
            device_count = torch.cuda.device_count()
            print(f"   CUDA devices in container: {device_count}")
            
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                print(f"     Device {i}: {device_name}")
                
    except Exception as e:
        print(f"   ❌ Error checking CUDA in container: {e}")

def main():
    """Run all Jetson detection diagnostics"""
    print("🚀 Jetson Detection Debug")
    print("=" * 50)
    
    check_jetson_indicators()
    test_offline_storage_detection()
    check_docker_environment()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    # Final test
    try:
        from offline_storage_manager import offline_storage
        is_jetson = offline_storage.is_jetson_device()
        capabilities = offline_storage.get_device_capabilities()
        
        print(f"Final Jetson Detection: {is_jetson}")
        print(f"Offline Processing Supported: {capabilities.get('offline_processing_supported')}")
        
        if is_jetson:
            print("✅ Jetson detected correctly!")
        else:
            print("❌ Jetson not detected - check the indicators above")
            
    except Exception as e:
        print(f"❌ Error in final test: {e}")

if __name__ == "__main__":
    main() 