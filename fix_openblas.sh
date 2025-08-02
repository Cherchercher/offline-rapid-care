#!/bin/bash

# Fix OpenBLAS library issue on Jetson
echo "🔧 Fixing OpenBLAS library issue on Jetson..."

# Check if we're on Jetson
if [ -f "/etc/nv_tegra_release" ]; then
    echo "✅ Confirmed Jetson device"
else
    echo "❌ Not running on Jetson device"
    exit 1
fi

# Install OpenBLAS
echo "📦 Installing OpenBLAS..."
sudo apt update
sudo apt install -y libopenblas-dev libopenblas-base

# Create symbolic link if needed
if [ ! -f "/usr/lib/aarch64-linux-gnu/libopenblas.so.0" ]; then
    echo "🔗 Creating symbolic link for libopenblas.so.0..."
    sudo ln -sf /usr/lib/aarch64-linux-gnu/libopenblas.so /usr/lib/aarch64-linux-gnu/libopenblas.so.0
fi

# Update library cache
echo "🔄 Updating library cache..."
sudo ldconfig

# Test PyTorch import
echo "🧪 Testing PyTorch import..."
python3 -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ PyTorch import successful!"
else
    echo "❌ PyTorch import still failing"
fi

echo "🔧 OpenBLAS fix completed!" 