# Multi-stage Dockerfile for EC2/Standard GPUs
# Stage 1: Standard Python base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONPATH=/workspace
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

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
ENV PIP_CACHE_DIR=/root/.cache/pip

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and build tools
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch >= 2.1 with CUDA support for standard GPUs
RUN pip3 install --no-cache-dir \
    torch>=2.1.0 \
    torchvision>=0.16.0 \
    torchaudio>=2.1.0 \
    --index-url https://download.pytorch.org/whl/cu118

# Install all requirements from requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install additional dependencies that might be needed
RUN pip3 install --no-cache-dir \
    pyaudio \
    psycopg2-binary \
    opencv-python-headless \
    sentence-transformers

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

# Default command
CMD ["python3", "app.py"] 


