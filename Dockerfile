# Multi-stage Dockerfile for Jetson Xavier
# Stage 1: Use official Jetson PyTorch base image
# https://catalog.ngc.nvidia.com/orgs/nvidia/containers/l4t-pytorch
FROM nvcr.io/nvidia/l4t-pytorch:r35.1.0-pth1.13-py3

# Test base image CUDA and PyTorch GPU availability
RUN echo "🔍 Testing base image CUDA/GPU availability..." && \
    echo "================================================" && \
    echo "Python version:" && python3 --version && \
    echo "================================================" && \
    echo "NVIDIA-SMI test:" && \
    (nvidia-smi || echo "❌ nvidia-smi not available in base image") && \
    echo "================================================" && \
    echo "NVCC test:" && \
    (nvcc --version || echo "❌ nvcc not available in base image") && \
    echo "================================================" && \
    echo "PyTorch CUDA test:" && \
    python3 -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA compiled version:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available()); print('CUDA device count:', torch.cuda.device_count()); print('CUDA device name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')" && \
    echo "================================================" && \
    echo "✅ Base image CUDA/GPU test complete" && \
    echo "================================================"

# # Stage 2: Transformers image
# FROM dustynv/transformers:r36.4.2 as transformers-base

# # Stage 3: Final application image
# FROM dustynv/transformers:r36.4.2

# Set environment variables
ENV PYTHONPATH=/workspace
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# CUDA environment variables for GPU detection
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}
ENV TORCH_CUDA_ARCH_LIST="5.3;6.2;7.2"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    libopenblas-dev \
    liblapack-dev \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    curl \
    build-essential \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    libffi-dev \
    liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# Build and install Python 3.9 from source (needed for newer transformers)
RUN cd /tmp && \
    wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz && \
    tar -xzf Python-3.9.18.tgz && \
    cd Python-3.9.18 && \
    ./configure --enable-optimizations --with-ensurepip=install --prefix=/usr/local && \
    make -j$(nproc) && \
    make altinstall && \
    cd / && \
    rm -rf /tmp/Python-3.9.18*

# Create symlinks for python3.9
RUN ln -sf /usr/local/bin/python3.9 /usr/local/bin/python3 && \
    ln -sf /usr/local/bin/pip3.9 /usr/local/bin/pip3

# Update PATH to use Python 3.9
ENV PATH="/usr/local/bin:$PATH"

# Test CUDA and PyTorch after Python 3.9 installation
RUN echo "🔍 Testing CUDA/GPU after Python 3.9 installation..." && \
    echo "================================================" && \
    echo "Python version after upgrade:" && python3 --version && \
    echo "Which python3:" && which python3 && \
    echo "Python3 executable:" && ls -la /usr/local/bin/python3 && \
    echo "================================================" && \
    echo "Testing PyTorch import with Python 3.9:" && \
    (python3 -c "import torch; print('✅ PyTorch imported with Python 3.9'); print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('CUDA device count:', torch.cuda.device_count())" || echo "❌ PyTorch not available with Python 3.9 - will need to reinstall") && \
    echo "================================================" && \
    echo "✅ Python 3.9 CUDA/GPU test complete" && \
    echo "================================================"


# Install newer SQLite for ChromaDB compatibility
RUN cd /tmp && \
    wget https://www.sqlite.org/2023/sqlite-autoconf-3420000.tar.gz && \
    tar -xzf sqlite-autoconf-3420000.tar.gz && \
    cd sqlite-autoconf-3420000 && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/sqlite-autoconf-3420000*

# Update library path for new SQLite
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Set working directory
WORKDIR /workspace

# No pip cache (using --no-cache-dir for fresh installs)

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and build tools
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Install all requirements from requirements.txt (includes unsloth and all other Python deps)
RUN pip3 install --no-cache-dir -r requirements.txt

# Final CUDA and PyTorch test after all installations
RUN echo "🔍 Final CUDA/GPU test after all requirements installed..." && \
    echo "================================================" && \
    echo "Final Python version:" && python3 --version && \
    echo "================================================" && \
    echo "Final PyTorch test:" && \
    python3 -c "import torch; print('✅ Final PyTorch test'); print('PyTorch version:', torch.__version__); print('CUDA compiled version:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available()); print('CUDA device count:', torch.cuda.device_count()); print('GPU detected:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No GPU - needs runtime access')" && \
    echo "================================================" && \
    echo "Testing other key imports:" && \
    python3 -c "import transformers; print('✅ transformers version:', transformers.__version__); import accelerate; print('✅ accelerate imported'); exec('try:\\n    import unsloth; print(\\\"✅ unsloth imported\\\")\\nexcept:\\n    print(\\\"⚠️ unsloth import failed\\\")')" && \
    echo "================================================" && \
    echo "✅ Final installation test complete" && \
    echo "================================================"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads models static templates

# Set permissions
RUN chmod +x *.py *.sh

# Expose port
EXPOSE 5050

# Set environment variables for the application
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1

# Test GPU detection script
RUN echo '#!/bin/bash\necho "🔍 Testing GPU detection..."\npython3 -c "import torch; print(f\"PyTorch version: {torch.__version__}\"); print(f\"CUDA available: {torch.cuda.is_available()}\"); print(f\"CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}\"); print(f\"Device count: {torch.cuda.device_count()}\"); print(f\"Device name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}\")"\necho "✅ GPU test complete"' > /workspace/test_gpu.sh && chmod +x /workspace/test_gpu.sh

# Default command
CMD ["python3", "app.py"] 


