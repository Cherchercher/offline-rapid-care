#!/bin/bash

# RapidCare TMUX Stop Script
# This script stops all RapidCare services running in tmux sessions

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
print_status "Stopping RapidCare tmux sessions..."

# Stop uploads server session
if tmux has-session -t rapidcare-uploads 2>/dev/null; then
    print_status "Stopping rapidcare-uploads session..."
    tmux kill-session -t rapidcare-uploads
    print_success "rapidcare-uploads session stopped"
else
    print_warning "rapidcare-uploads session not found"
fi

# Stop model manager session
if tmux has-session -t rapidcare-model 2>/dev/null; then
    print_status "Stopping rapidcare-model session..."
    tmux kill-session -t rapidcare-model
    print_success "rapidcare-model session stopped"
else
    print_warning "rapidcare-model session not found"
fi

# Stop Flask app session
if tmux has-session -t rapidcare-app 2>/dev/null; then
    print_status "Stopping rapidcare-app session..."
    tmux kill-session -t rapidcare-app
    print_success "rapidcare-app session stopped"
else
    print_warning "rapidcare-app session not found"
fi

print_success "All RapidCare tmux sessions stopped"
echo ""
echo "📋 Remaining tmux sessions:"
tmux list-sessions 2>/dev/null || echo "No tmux sessions running"
echo ""
echo "🔍 Checking for remaining processes on RapidCare ports..."
if lsof -ti:11435 > /dev/null 2>&1; then
    echo "⚠️  Process still running on port 11435 (uploads server)"
fi
if lsof -ti:5050 > /dev/null 2>&1; then
    echo "⚠️  Process still running on port 5050 (Flask app)"
fi
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "⚠️  Process still running on port 5001 (model API server)"
fi 