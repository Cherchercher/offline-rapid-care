#!/bin/bash

echo "🔍 Checking Container Status and API"
echo "==================================="

# Check if container is running
echo "📊 Container Status:"
if sudo docker ps | grep -q offline-gemma-jetson; then
    echo "✅ Container is running"
    sudo docker ps | grep offline-gemma-jetson
else
    echo "❌ Container is not running"
    echo "📋 Recent container logs:"
    sudo docker logs offline-gemma-jetson --tail 20
    exit 1
fi

echo ""

# Check container logs for startup messages
echo "📋 Container Logs (last 30 lines):"
sudo docker logs offline-gemma-jetson --tail 30

echo ""

# Test the API endpoint
echo "🌐 Testing API Endpoint:"
curl -s http://localhost:5050/api/device/capabilities | python3 -m json.tool 2>/dev/null || echo "❌ API not responding"

echo ""

# Check what's running inside the container
echo "🐳 Container Environment Check:"
sudo docker exec offline-gemma-jetson python3 -c "
import os
import torch

print('Jetson files in container:')
jetson_files = ['/etc/nv_tegra_release', '/proc/device-tree/model']
for file in jetson_files:
    if os.path.exists(file):
        print(f'  ✅ {file} - EXISTS')
        try:
            with open(file, 'r') as f:
                content = f.read().strip()
                print(f'     Content: {content}')
        except Exception as e:
            print(f'     Error reading: {e}')
    else:
        print(f'  ❌ {file} - NOT FOUND')

print('\\nCUDA in container:')
print(f'  CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  Device Count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        device_name = torch.cuda.get_device_name(i)
        print(f'  Device {i}: {device_name}')
        device_lower = device_name.lower()
        if 'tegra' in device_lower or 'jetson' in device_lower:
            print(f'    ✅ Jetson keywords found')
        else:
            print(f'    ❌ No Jetson keywords')
else:
    print('  ❌ No CUDA available')
"

echo ""

# Check if the app.py changes are in the container
echo "📝 Checking app.py in container:"
sudo docker exec offline-gemma-jetson grep -n "host.*0.0.0.0" /workspace/app.py || echo "❌ Host binding not found in container app.py" 