#!/bin/bash

# RapidCare TMUX Stop Script
# This script stops all RapidCare services running in tmux sessions

set -e

echo "🛑 RapidCare - TMUX Stop"
echo "========================"

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

# Stop all RapidCare tmux sessions
stop_sessions() {
    print_status "Stopping RapidCare tmux sessions..."
    
    # Stop each session if it exists
    if tmux has-session -t rapidcare-uploads 2>/dev/null; then
        print_status "Stopping uploads server session..."
        tmux kill-session -t rapidcare-uploads
        print_success "Uploads server session stopped"
    else
        print_warning "Uploads server session not found"
    fi
    
    if tmux has-session -t rapidcare-app 2>/dev/null; then
        print_status "Stopping Flask app session..."
        tmux kill-session -t rapidcare-app
        print_success "Flask app session stopped"
    else
        print_warning "Flask app session not found"
    fi
}

# Kill any remaining processes
kill_remaining_processes() {
    print_status "Checking for remaining RapidCare processes..."
    
    # Kill any remaining Python processes related to the app
    pkill -f "python.*app.py" 2>/dev/null || true
    pkill -f "python.*serve_uploads.py" 2>/dev/null || true
    
    print_success "Process cleanup completed"
}

# Show final status
show_final_status() {
    echo ""
    echo "🎯 Final Status Check:"
    echo "======================"
    echo ""
    
    # Check if sessions are still running
    if tmux list-sessions 2>/dev/null | grep -q rapidcare; then
        echo "⚠️  Some RapidCare sessions may still be running:"
        tmux list-sessions | grep rapidcare || true
    else
        echo "✅ All RapidCare tmux sessions stopped"
    fi
    
    # Check if services are still responding
    if curl -s http://localhost:11435 > /dev/null 2>&1; then
        echo "⚠️  Uploads server still responding"
    fi
    
    if curl -s http://localhost:5050 > /dev/null 2>&1; then
        echo "⚠️  Flask app still responding"
    fi
    
    echo ""
    echo "🔄 To restart all services:"
    echo "  ./tmux_start.sh"
    echo ""
}

# Main execution
main() {
    stop_sessions
    kill_remaining_processes
    show_final_status
    print_success "RapidCare services stopped successfully"
}

# Run main function
main "$@" 