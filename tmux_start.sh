#!/bin/bash

# RapidCare TMUX Startup Script
# This script starts all RapidCare services in tmux sessions for easy management

set -e

echo "🚑 RapidCare - TMUX Startup"
echo "============================"

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

# Check if tmux is installed
check_tmux() {
    if ! command -v tmux &> /dev/null; then
        print_error "tmux is not installed. Please install it first:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_error "  brew install tmux"
        else
            print_error "  sudo apt-get install tmux  # Ubuntu/Debian"
            print_error "  sudo yum install tmux      # CentOS/RHEL"
        fi
        exit 1
    fi
    print_success "tmux found: $(tmux -V)"
}

# Kill existing tmux sessions
cleanup_sessions() {
    print_status "Cleaning up existing tmux sessions..."
    tmux kill-session -t rapidcare-uploads 2>/dev/null || true
    tmux kill-session -t rapidcare-app 2>/dev/null || true
    tmux kill-session -t rapidcare-model 2>/dev/null || true
    print_success "Existing sessions cleaned up"
}

# Check local model availability
check_local_model() {
    print_status "Checking local Gemma 3n model..."
    
    local_model_path="./models/gemma3n-local-e2b"
    if [ -d "$local_model_path" ]; then
        print_success "Local Gemma 3n model found at $local_model_path"
        
        # Check for key model files
        if [ -f "$local_model_path/config.json" ] && [ -f "$local_model_path/model.safetensors.index.json" ]; then
            print_success "Model files verified"
        else
            print_warning "Some model files may be missing"
        fi
    else
        print_error "Local model not found at $local_model_path"
        print_error "Please run download_gemma_local.py first to download the model"
        exit 1
    fi
}

# Start uploads server in tmux
start_uploads_session() {
    print_status "Starting uploads server in tmux session..."
    
    # Create new tmux session for uploads server
    tmux new-session -d -s rapidcare-uploads -n uploads
    
    # Start uploads server
    tmux send-keys -t rapidcare-uploads:uploads "python3 serve_uploads.py" Enter
    
    # Wait for uploads server to start
    sleep 3
    if curl -s http://localhost:11435 > /dev/null 2>&1; then
        print_success "Uploads server started successfully"
    else
        print_warning "Uploads server may still be starting up..."
    fi
}

# Start model API server in separate tmux session
start_model_session() {
    print_status "Starting model API server in tmux session..."
    
    # Create new tmux session for model server
    tmux new-session -d -s rapidcare-model -n model
    
    # Start model API server
    tmux send-keys -t rapidcare-model:model "python3 model_server.py" Enter
    
    # Wait for model server to start
    sleep 5
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        print_success "Model API server started successfully"
    else
        print_warning "Model API server may still be starting up..."
    fi
    
    print_success "Model API server session created"
}

# Start Flask app in tmux
start_app_session() {
    print_status "Starting Flask application in tmux session..."
    
    # Create new tmux session for Flask app
    tmux new-session -d -s rapidcare-app -n app
    
    # Start Flask app
    tmux send-keys -t rapidcare-app:app "export FLASK_ENV=development" Enter
    tmux send-keys -t rapidcare-app:app "export FLASK_DEBUG=1" Enter
    tmux send-keys -t rapidcare-app:app "python3 app.py" Enter
    
    # Wait for Flask app to start
    sleep 5
    if curl -s http://localhost:5050 > /dev/null 2>&1; then
        print_success "Flask application started successfully"
    else
        print_warning "Flask app may still be starting up..."
    fi
}

# Show status and management commands
show_management_info() {
    echo ""
    echo "🎯 RapidCare Services Status:"
    echo "============================="
    echo ""
    
    # Check local model
    local_model_path="./models/gemma3n-local-e2b"
    if [ -d "$local_model_path" ]; then
        echo "✅ Local Gemma 3n Model: $local_model_path"
    else
        echo "❌ Local Model: Not found"
    fi
    
    # Check uploads server
    if curl -s http://localhost:11435 > /dev/null 2>&1; then
        echo "✅ Uploads Server: http://localhost:11435"
    else
        echo "❌ Uploads Server: Not responding"
    fi
    
    # Check Flask app
    if curl -s http://localhost:5050 > /dev/null 2>&1; then
        echo "✅ Flask App: http://localhost:5050"
    else
        echo "❌ Flask App: Not responding"
    fi
    
    # Check model API server
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        echo "✅ Model API Server: http://localhost:5001"
    else
        echo "❌ Model API Server: Not responding"
    fi
    
    echo ""
    echo "🔧 TMUX Management Commands:"
    echo "============================"
    echo ""
    echo "View all sessions:"
    echo "  tmux list-sessions"
    echo ""
    echo "Attach to specific sessions:"
    echo "  tmux attach-session -t rapidcare-uploads   # Uploads server"
    echo "  tmux attach-session -t rapidcare-app       # Flask app"
    echo "  tmux attach-session -t rapidcare-model     # Model API server"
    echo ""
    echo "Monitor all sessions:"
    echo "  tmux attach-session -t rapidcare-app       # Main app"
    echo ""
    echo "Stop all services:"
    echo "  ./tmux_stop.sh"
    echo ""
    echo "Test local model directly:"
    echo "  python3 model_server.py"
    echo ""
    echo "View logs in real-time:"
    echo "  tmux attach-session -t rapidcare-app"
    echo "  # Then use Ctrl+b, arrow keys to switch between panes"
    echo ""
    echo "📱 Access the application at: http://localhost:5050"
    echo ""
}

# Main execution
main() {
    check_tmux
    check_local_model
    cleanup_sessions
    start_uploads_session
    sleep 2
    start_model_session
    sleep 2
    start_app_session
    show_management_info
}

# Run main function
main "$@" 
