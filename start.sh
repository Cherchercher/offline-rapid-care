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



# Check if Gemma model is available
check_gemma_model() {
    print_status "Checking Gemma 3n model..."
    
    # Check if model directory exists
    if [ -d "./models/gemma3n-2b" ] || [ -d "./models/gemma3n-4b" ]; then
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
        print_warning "Gemma 3n model not found. Please download models first:"
        print_warning "python3 scripts/download_gemma_models.py --model both"
    fi
}

# Test if model is ready to respond
test_model_loading() {
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Testing model (attempt $attempt/$max_attempts)..."
        
        # Try a simple test request to the model server
        response=$(curl -s -X POST http://127.0.0.1:5001/chat \
            -H "Content-Type: application/json" \
            -d '{"messages": [{"role": "user", "content": "Hello"}]}' \
            --max-time 30 2>/dev/null)
        
        if echo "$response" | grep -q '"success"' && echo "$response" | grep -q '"response"'; then
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
    pkill -f "model_server" 2>/dev/null || true
    
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



# Start uploads server
start_uploads_server() {
    print_status "Starting uploads server for model access..."
    print_success "Uploads server will be available at: http://localhost:11435"
    
    # Start uploads server in background
    $PYTHON_CMD serve_uploads.py > /dev/null 2>&1 &
    UPLOADS_SERVER_PID=$!
    
    # Wait a moment for server to start
    sleep 2
    
    # Test if server is running
    if curl -s http://localhost:11435 > /dev/null 2>&1; then
        print_success "Uploads server started (PID: $UPLOADS_SERVER_PID)"
    else
        print_warning "Uploads server may take a moment to start"
    fi
}



# Start Flask application
start_flask() {
    print_status "Starting RapidCare application..."
    print_success "Application will be available at: http://localhost:5050"
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
    check_gemma_model
    install_dependencies
    generate_icons
    start_uploads_server
    start_flask
}

# Run main function
main "$@" 