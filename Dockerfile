# Multi-stage Dockerfile for Jetson Xavier
# Stage 1: Base PyTorch image
FROM nvcr.io/nvidia/l4t-pytorch:r35.1.0-pth1.11-py3 as pytorch-base

# # Stage 2: Transformers image
# FROM dustynv/transformers:r36.4.2 as transformers-base

# # Stage 3: Final application image
# FROM dustynv/transformers:r36.4.2

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
    build-essential \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    libffi-dev \
    liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# Build and install Python 3.9 from source
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

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with better error handling
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel
RUN pip3 install --no-cache-dir backports.zoneinfo==0.2.1
RUN pip3 install --no-cache-dir -r requirements.txt

# Fix numpy compatibility issue with OpenCV
RUN pip3 install --no-cache-dir "numpy>=1.24.0,<2.0.0"

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

