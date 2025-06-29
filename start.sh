#!/bin/bash

# RapidCare Startup Script
# This script sets up and starts the RapidCare PWA application

set -e

echo "🚑 RapidCare - MCI Response System"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    else
        OS="unknown"
    fi
    print_status "Detected OS: $OS"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8+"
        exit 1
    fi
    print_success "Python found: $($PYTHON_CMD --version)"
}

# Check if Ollama is installed
check_ollama() {
    print_status "Checking Ollama installation..."
    if ! command -v ollama &> /dev/null; then
        print_warning "Ollama not found. Installing Ollama..."
        if [[ "$OS" == "macos" ]]; then
            # Check if Homebrew is available
            if command -v brew &> /dev/null; then
                print_status "Installing Ollama via Homebrew..."
                brew install ollama
            else
                print_error "Homebrew not found. Please install Ollama manually:"
                print_error "1. Visit https://ollama.ai/download"
                print_error "2. Download and install the macOS version"
                print_error "3. Or install Homebrew and run: brew install ollama"
                exit 1
            fi
        else
            # Linux installation
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
        print_success "Ollama installed successfully"
    else
        print_success "Ollama found: $(ollama --version)"
    fi
}

# Check if Gemma model is available
check_gemma_model() {
    print_status "Checking Gemma 3n model..."
    # First check if Ollama server is running
    if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        print_warning "Ollama server not running. Starting it..."
        start_ollama
        sleep 3
    fi
    
    # Check if model exists
    if ollama list | grep -q "gemma3n:e4b"; then
        print_success "Gemma 3n model found"
        
        # Test model loading with a simple request
        print_status "Testing model loading..."
        if test_model_loading; then
            print_success "Model is ready for use"
        else
            print_warning "Model may need to be reloaded. This can take a few minutes..."
            reload_model
        fi
    else
        print_warning "Gemma 3n model not found. Downloading..."
        ollama pull gemma3n:e4b
        print_success "Gemma 3n model downloaded successfully"
    fi
}

# Test if model is ready to respond
test_model_loading() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Testing model (attempt $attempt/$max_attempts)..."
        
        # Try a simple test request
        response=$(curl -s -X POST http://127.0.0.1:11434/api/chat \
            -H "Content-Type: application/json" \
            -d '{
                "model": "gemma3n:e4b",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": false
            }' --max-time 30 2>/dev/null)
        
        if echo "$response" | grep -q '"message"' && echo "$response" | grep -q '"content"'; then
            return 0
        fi
        
        print_warning "Model not ready yet, waiting..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    return 1
}

# Reload the model
reload_model() {
    print_status "Reloading Gemma 3n model..."
    
    # Stop any existing model processes
    pkill -f "ollama.*gemma3n" 2>/dev/null || true
    
    # Wait a moment
    sleep 2
    
    # Try to load the model again
    if test_model_loading; then
        print_success "Model reloaded successfully"
    else
        print_warning "Model may take longer to load on first use"
    fi
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            print_status "Creating virtual environment..."
            $PYTHON_CMD -m venv venv
        fi
        
        # Activate virtual environment
        print_status "Activating virtual environment..."
        source venv/bin/activate
        
        # Upgrade pip
        $PYTHON_CMD -m pip install --upgrade pip
        
        # Install dependencies
        $PYTHON_CMD -m pip install -r requirements.txt
        print_success "Dependencies installed successfully"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Generate icons if they don't exist
generate_icons() {
    print_status "Checking PWA icons..."
    if [ ! -f "static/images/icon-192x192.png" ]; then
        print_warning "PWA icons not found. Generating..."
        if command -v $PYTHON_CMD &> /dev/null; then
            $PYTHON_CMD -c "import PIL" 2>/dev/null || {
                print_status "Installing Pillow for icon generation..."
                $PYTHON_CMD -m pip install Pillow
            }
            $PYTHON_CMD generate_icons.py
            print_success "Icons generated successfully"
        else
            print_warning "Could not generate icons. Please run 'python generate_icons.py' manually"
        fi
    else
        print_success "PWA icons found"
    fi
}

# Start Ollama service
start_ollama() {
    print_status "Starting Ollama service..."
    if ! pgrep -x "ollama" > /dev/null; then
        # Start Ollama in background
        ollama serve > /dev/null 2>&1 &
        OLLAMA_PID=$!
        
        # Wait for Ollama to start
        print_status "Waiting for Ollama to start..."
        for i in {1..10}; do
            if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
                print_success "Ollama service started (PID: $OLLAMA_PID)"
                return 0
            fi
            sleep 1
        done
        print_error "Failed to start Ollama service"
        exit 1
    else
        print_success "Ollama service already running"
    fi
}

# Start Flask application
start_flask() {
    print_status "Starting RapidCare application..."
    print_success "Application will be available at: http://localhost:5000"
    print_success "Press Ctrl+C to stop the application"
    echo ""
    
    # Set Flask environment
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    
    # Start Flask app
    $PYTHON_CMD app.py
}

# Cleanup function
cleanup() {
    print_status "Shutting down..."
    if [ ! -z "$OLLAMA_PID" ]; then
        kill $OLLAMA_PID 2>/dev/null || true
        print_success "Ollama service stopped"
    fi
    print_success "RapidCare shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    echo ""
    detect_os
    check_python
    check_ollama
    check_gemma_model
    install_dependencies
    generate_icons
    start_ollama
    start_flask
}

# Run main function
main "$@" 